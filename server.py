from datetime import date, datetime, time, timedelta
from flask import Flask, jsonify, request, render_template, send_file
from io import StringIO, BytesIO
import csv

from database.db import fetch_all, execute
from dm_logic.study_order import eligible_topics, topological_order
from dm_logic.conflicts import find_conflicts
from dm_logic.workload import check_workload
from dm_logic.recurrence import generate_review_schedule
from dm_logic.auto_schedule import get_free_time_slots

app = Flask(__name__)

ROUTINE_CATEGORIES = {'Sleep','Meal','Snack','Break','College','Tuition','Exercise','Nap','Personal','Other'}
EVENT_CATEGORIES = {'College','Tuition','Commute','Going out','Appointment','Exercise','Personal','Other'}
SESSION_STATUSES = {'Planned','Done','Skipped'}



def iso(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, timedelta):
        total = int(v.total_seconds())
        return f"{total//3600:02d}:{(total%3600)//60:02d}"
    return v


def rows_dict(rows, keys):
    return [dict(zip(keys, [iso(v) for v in row])) for row in rows]


def json_error(message, status=400):
    return jsonify({"error": message}), status


def parse_dt(value):
    if not value:
        return None
    return datetime.fromisoformat(value)


def get_topics():
    return fetch_all("""
        SELECT t.topic_id,t.subject_id,s.name,t.name,t.status,t.estimated_minutes,t.parent_topic_id
        FROM topics t JOIN subjects s ON s.subject_id=t.subject_id
        ORDER BY s.name,t.name
    """)


def topic_payload(row):
    return {
        "id": row[0], "subject_id": row[1], "subject": row[2], "name": row[3],
        "status": row[4], "minutes": row[5], "parent_topic_id": row[6]
    }


def build_plan(days=7, start_date=None):
    start_date = start_date or date.today()
    end_date = start_date + timedelta(days=max(1, min(days, 31)) - 1)
    topics = get_topics()
    prereq_rows = fetch_all("SELECT topic_id, prerequisite_topic_id FROM topic_prerequisites")
    prereqs = {}
    edges = []
    for topic_id, prerequisite_id in prereq_rows:
        prereqs.setdefault(topic_id, []).append(prerequisite_id)
        edges.append((prerequisite_id, topic_id))
    ids = [r[0] for r in topics]
    completed = [r[0] for r in topics if r[4] == "Completed"]
    eligible = eligible_topics(ids, completed, prereqs)
    eligible_set = set(eligible)

    topic_by_id = {r[0]: topic_payload(r) for r in topics}
    try:
        topo = topological_order(ids, edges)
    except ValueError:
        topo = ids
    topo_rank = {tid: i for i, tid in enumerate(topo)}

    exams = fetch_all("SELECT e.exam_id,e.subject_id,s.name,e.title,e.starts_at FROM exams e JOIN subjects s ON s.subject_id=e.subject_id WHERE e.starts_at BETWEEN %s AND %s ORDER BY e.starts_at", (datetime.combine(start_date, time.min), datetime.combine(end_date + timedelta(days=1), time.min)))
    tasks = fetch_all("SELECT task_id,title,subject_id,due_at,priority,status FROM tasks WHERE status <> 'Done' AND (due_at IS NULL OR due_at <= %s) ORDER BY due_at IS NULL,due_at", (datetime.combine(end_date + timedelta(days=1), time.min),))

    pressure = {}
    for _, subject_id, _, _, starts_at in exams:
        days_left = max(0, (starts_at.date() - start_date).days)
        pressure[subject_id] = max(pressure.get(subject_id, 0), 100 - days_left * 8)
    for _, _, subject_id, due_at, priority, _ in tasks:
        if subject_id:
            days_left = 14 if due_at is None else max(0, (due_at.date() - start_date).days)
            p = {"High": 35, "Medium": 20, "Low": 10}.get(priority, 10) + max(0, 30 - days_left * 3)
            pressure[subject_id] = max(pressure.get(subject_id, 0), p)

    candidates = [topic_by_id[i] for i in eligible_set]
    candidates = [c for c in candidates if c["minutes"] > 0]
    
    def sort_candidates():
        candidates.sort(key=lambda t: (-pressure.get(t["subject_id"], 0), topo_rank.get(t["id"], 9999), -t["minutes"]))
        
    sort_candidates()

    scheduled = []
    reasons = []
    total_available = 0

    from dm_logic.auto_schedule import timedelta_to_time

    for offset in range((end_date - start_date).days + 1):
        day = start_date + timedelta(days=offset)
        
        day_start = datetime.combine(day, time(7, 0))
        day_end = datetime.combine(day, time(23, 0))
        # Never create study sessions in the past when generating today's plan.
        if day == date.today():
            now = datetime.now()
            if now >= day_end:
                continue
            if now > day_start:
                minute = ((now.minute + 4) // 5) * 5
                rounded_now = now.replace(second=0, microsecond=0) + timedelta(minutes=(minute - now.minute))
                day_start = max(day_start, rounded_now)
        
        events = fetch_all("SELECT starts_at,ends_at FROM events WHERE starts_at <= %s AND ends_at >= %s", (day_end, day_start))
        
        sessions = fetch_all("SELECT starts_at,ends_at FROM study_sessions WHERE starts_at <= %s AND ends_at >= %s AND status IN ('Planned', 'Done')", (day_end, day_start))
        
        exams_list = fetch_all("SELECT starts_at,DATE_ADD(starts_at, INTERVAL 2 HOUR) FROM exams WHERE starts_at <= %s AND DATE_ADD(starts_at, INTERVAL 2 HOUR) >= %s", (day_end, day_start))
        
        routines_raw = fetch_all("SELECT weekday, starts_at, ends_at FROM routine_blocks WHERE enabled=1")
        routines = []
        for r_weekday, r_start, r_end in routines_raw:
            if r_weekday == day.weekday():
                routines.append((datetime.combine(day, timedelta_to_time(r_start)), datetime.combine(day, timedelta_to_time(r_end))))
            if r_weekday == (day.weekday() - 1) % 7 and r_end < r_start:
                routines.append((datetime.combine(day - timedelta(days=1), timedelta_to_time(r_start)), datetime.combine(day, timedelta_to_time(r_end))))
        
        free = get_free_time_slots(day, routines, events, sessions + exams_list)
        scheduled_today = set()
        
        bounded = []
        for a, b in free:
            if b > a and (b-a).total_seconds() >= 25*60:
                bounded.append((a,b))
                
        total_available += sum(int((b-a).total_seconds()//60) for a,b in bounded)
        
        for a, b in bounded:
            while candidates and a < b:
                topic_idx = 0
                duration = 0
                while topic_idx < len(candidates):
                    topic = candidates[topic_idx]
                    if topic["id"] in scheduled_today:
                        topic_idx += 1
                        continue
                    duration = min(topic["minutes"], 60)
                    if a + timedelta(minutes=duration) <= b:
                        break
                    if (b - a).total_seconds() >= 25 * 60:
                        duration = int((b - a).total_seconds() // 60)
                        break
                    topic_idx += 1
                
                if topic_idx >= len(candidates):
                    break
                
                topic = candidates.pop(topic_idx)
                end = a + timedelta(minutes=duration)
                
                scheduled.append({
                    "title": topic["name"], "topic_id": topic["id"], "subject": topic["subject"],
                    "starts_at": a, "ends_at": end, "minutes": duration, "kind": "Study",
                    "reason": "Scheduled to fit availability"
                })
                
                topic["minutes"] -= duration
                scheduled_today.add(topic["id"])
                if topic["minutes"] > 0:
                    candidates.append(topic)
                    sort_candidates()
                
                a = end + timedelta(minutes=10)

    remaining = candidates[:]
    required = sum(max(0, t["minutes"]) for t in candidates)
    overloaded, proof = check_workload(required, total_available)
    reasons.extend([
        f"{len(eligible_set)} topic(s) are currently eligible based on completed prerequisites.",
        f"The planner searched {total_available} minutes of realistic study availability inside the 07:00–23:00 study window.",
        "Topics are fragmented properly to pack into available gaps, ignoring rigid daily repeats.",
        "Upcoming exams and deadlines increase subject priority, and exams block free time.",
    ])
    if remaining:
        reasons.append(f"{len(remaining)} topic(s) could not fit; they remain unscheduled instead of being placed over commitments.")
    return scheduled, remaining, {"overloaded": overloaded, "proof": proof, "reasons": reasons, "available_minutes": total_available, "eligible_topics": len(eligible_set)}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/dashboard")
def dashboard():
    today = date.today()
    tasks = fetch_all("SELECT COUNT(*) FROM tasks WHERE status <> 'Done'")[0][0]
    exams = fetch_all("SELECT COUNT(*) FROM exams WHERE starts_at >= %s AND starts_at < %s", (datetime.combine(today,time.min), datetime.combine(today+timedelta(days=30),time.min)))[0][0]
    completed = fetch_all("SELECT COUNT(*) FROM topics WHERE status='Completed'")[0][0]
    total = fetch_all("SELECT COUNT(*) FROM topics")[0][0]
    sessions = fetch_all("SELECT session_id,title,starts_at,ends_at,status FROM study_sessions WHERE DATE(starts_at)=%s ORDER BY starts_at", (today,))
    next_up = None
    upcoming = [s for s in sessions if s[4] == 'Planned']
    if upcoming:
        s=upcoming[0]; next_up={"id":s[0],"title":s[1],"start":iso(s[2]),"end":iso(s[3])}
    return jsonify({"today":today.isoformat(),"tasks":tasks,"exams":exams,"completed_topics":completed,"total_topics":total,"progress":round(completed/total*100) if total else 0,"sessions":rows_dict(sessions,["id","title","start","end","status"]),"next":next_up})


@app.route("/api/subjects", methods=["GET","POST"])
def subjects():
    if request.method == "POST":
        d=request.json or {}; name=(d.get("name") or '').strip()
        if not name: return json_error("Subject name is required")
        sid=execute("INSERT INTO subjects(name,description,color) VALUES(%s,%s,%s)",(name,d.get("description",""),d.get("color","#7c3aed")))
        return jsonify({"id":sid}),201
    rows=fetch_all("SELECT subject_id,name,description,color FROM subjects ORDER BY name")
    return jsonify(rows_dict(rows,["id","name","description","color"]))


@app.route("/api/subjects/<int:sid>", methods=["DELETE"])
def delete_subject(sid):
    execute("DELETE FROM subjects WHERE subject_id=%s",(sid,)); return jsonify({"ok":True})


@app.get("/api/topics")
def topics():
    return jsonify([topic_payload(r) for r in get_topics()])


@app.post("/api/topics")
def add_topic():
    d=request.json or {}; name=(d.get("name") or '').strip(); subject_id=d.get("subject_id")
    if not name or not subject_id: return json_error("Topic name and subject are required")
    tid=execute("INSERT INTO topics(subject_id,name,estimated_minutes) VALUES(%s,%s,%s)",(subject_id,name,max(5,int(d.get("minutes",45)))))
    return jsonify({"id":tid}),201


@app.route("/api/topics/<int:tid>", methods=["PATCH"])
def update_topic(tid):
    d=request.json or {}; fields=[]; vals=[]
    for key,col in [("name","name"),("status","status"),("minutes","estimated_minutes")]:
        if key in d:
            fields.append(f"{col}=%s"); vals.append(d[key])
    if not fields: return json_error("Nothing to update")
    vals.append(tid); execute(f"UPDATE topics SET {','.join(fields)} WHERE topic_id=%s",tuple(vals)); return jsonify({"ok":True})


@app.get("/api/prerequisites")
def prerequisites():
    rows=fetch_all("SELECT tp.topic_id,tp.prerequisite_topic_id,t.name,p.name FROM topic_prerequisites tp JOIN topics t ON t.topic_id=tp.topic_id JOIN topics p ON p.topic_id=tp.prerequisite_topic_id ORDER BY t.name,p.name")
    return jsonify(rows_dict(rows,["topic_id","prerequisite_id","topic","prerequisite"]))


@app.post("/api/prerequisites")
def add_prerequisite():
    d=request.json or {}; topic=int(d.get("topic_id")); prereq=int(d.get("prerequisite_id"))
    if topic==prereq:return json_error("A topic cannot depend on itself")
    current=fetch_all("SELECT topic_id,prerequisite_topic_id FROM topic_prerequisites")
    topics=[r[0] for r in get_topics()]; proposed=[(p,t) for t,p in current if t!=topic]+[(prereq,topic)]
    try: topological_order(topics,proposed)
    except ValueError as e: return json_error(str(e))
    execute("INSERT IGNORE INTO topic_prerequisites(topic_id,prerequisite_topic_id) VALUES(%s,%s)",(topic,prereq)); return jsonify({"ok":True})


@app.route("/api/prerequisites", methods=["DELETE"])
def delete_prerequisite():
    d=request.json or {}; execute("DELETE FROM topic_prerequisites WHERE topic_id=%s AND prerequisite_topic_id=%s",(d.get("topic_id"),d.get("prerequisite_id"))); return jsonify({"ok":True})


@app.route("/api/tasks", methods=["GET","POST"])
def tasks():
    if request.method=="POST":
        d=request.json or {}; title=(d.get("title") or '').strip()
        if not title:return json_error("Task title is required")
        tid=execute("INSERT INTO tasks(title,subject_id,due_at,priority,status,notes) VALUES(%s,%s,%s,%s,%s,%s)",(title,d.get("subject_id"),parse_dt(d.get("due_at")),d.get("priority","Medium"),d.get("status","To do"),d.get("notes","")))
        return jsonify({"id":tid}),201
    rows=fetch_all("SELECT t.task_id,t.title,t.subject_id,s.name,t.due_at,t.priority,t.status,t.notes FROM tasks t LEFT JOIN subjects s ON s.subject_id=t.subject_id ORDER BY t.due_at IS NULL,t.due_at")
    return jsonify(rows_dict(rows,["id","title","subject_id","subject","due_at","priority","status","notes"]))


@app.route("/api/tasks/<int:tid>", methods=["PATCH"])
def update_task(tid):
    d=request.json or {}; status=d.get("status")
    if status not in {"To do","In progress","Done"}: return json_error("Invalid status")
    execute("UPDATE tasks SET status=%s WHERE task_id=%s",(status,tid)); return jsonify({"ok":True})


@app.route("/api/exams", methods=["GET","POST"])
def exams():
    if request.method=="POST":
        d=request.json or {}; title=(d.get("title") or '').strip()
        if not title or not d.get("subject_id") or not d.get("starts_at"): return json_error("Exam title, subject and date are required")
        eid=execute("INSERT INTO exams(subject_id,title,starts_at,location,notes) VALUES(%s,%s,%s,%s,%s)",(d["subject_id"],title,parse_dt(d["starts_at"]),d.get("location",""),d.get("notes","")))
        return jsonify({"id":eid}),201
    rows=fetch_all("SELECT e.exam_id,e.subject_id,s.name,e.title,e.starts_at,e.location FROM exams e JOIN subjects s ON s.subject_id=e.subject_id ORDER BY e.starts_at")
    return jsonify(rows_dict(rows,["id","subject_id","subject","title","starts_at","location"]))


@app.route("/api/routine", methods=["GET","POST"])
def routine():
    if request.method=="POST":
        d=request.json or {}
        title=(d.get("title") or "").strip()
        starts_at=d.get("starts_at")
        ends_at=d.get("ends_at")
        try:
            weekday=int(d["weekday"])
        except (KeyError, TypeError, ValueError):
            return json_error("A valid weekday is required")
        if not title or not starts_at or not ends_at:
            return json_error("Routine title, start time, and end time are required")
        if weekday not in range(7):
            return json_error("Weekday must be between 0 and 6")
        if ends_at <= starts_at:
            return json_error("End time must be after start time")
        category = d.get("category","Other")
        if category not in ROUTINE_CATEGORIES:
            return json_error("Invalid routine category. Choose from: " + ", ".join(sorted(ROUTINE_CATEGORIES)))
        rid=execute("INSERT INTO routine_blocks(weekday,title,category,starts_at,ends_at) VALUES(%s,%s,%s,%s,%s)",(weekday,title,category,starts_at,ends_at))
        return jsonify({"id":rid}),201
    rows=fetch_all("SELECT routine_id,weekday,title,category,starts_at,ends_at FROM routine_blocks WHERE enabled=1 ORDER BY weekday,starts_at")
    return jsonify(rows_dict(rows,["id","weekday","title","category","starts_at","ends_at"]))


@app.route("/api/events", methods=["GET","POST"])
def events():
    if request.method=="POST":
        d=request.json or {}; title=(d.get("title") or "").strip()
        if not title or not d.get("starts_at") or not d.get("ends_at"):
            return json_error("Event title, start, and end are required")
        starts=parse_dt(d["starts_at"]); ends=parse_dt(d["ends_at"])
        if not starts or not ends or ends <= starts:
            return json_error("Event end must be after its start")
        category=d.get("category","Other")
        if category not in EVENT_CATEGORIES:
            return json_error("Invalid event category. Choose from: " + ", ".join(sorted(EVENT_CATEGORIES)))
        eid=execute("INSERT INTO events(title,category,starts_at,ends_at,location,notes) VALUES(%s,%s,%s,%s,%s,%s)",(title,category,starts,ends,d.get("location",""),d.get("notes","")))
        return jsonify({"id":eid}),201
    rows=fetch_all("SELECT event_id,title,category,starts_at,ends_at,location FROM events WHERE ends_at >= %s ORDER BY starts_at LIMIT 200",(datetime.now(),))
    return jsonify(rows_dict(rows,["id","title","category","starts_at","ends_at","location"]))


@app.route("/api/sessions", methods=["GET","POST"])
def sessions():
    if request.method=="POST":
        d=request.json or {}; title=(d.get("title") or "").strip()
        starts=parse_dt(d.get("starts_at")); ends=parse_dt(d.get("ends_at")); status=d.get("status","Planned")
        if not title or not starts or not ends:
            return json_error("Session title, start, and end are required")
        if ends <= starts:
            return json_error("Session end must be after its start")
        if status not in SESSION_STATUSES:
            return json_error("Invalid session status")
        sid=execute("INSERT INTO study_sessions(title,topic_id,task_id,starts_at,ends_at,status) VALUES(%s,%s,%s,%s,%s,%s)",(title,d.get("topic_id"),d.get("task_id"),starts,ends,status))
        return jsonify({"id":sid}),201
    rows=fetch_all("SELECT session_id,title,topic_id,task_id,starts_at,ends_at,status FROM study_sessions ORDER BY starts_at DESC LIMIT 300")
    return jsonify(rows_dict(rows,["id","title","topic_id","task_id","starts_at","ends_at","status"]))


@app.route("/api/sessions/<int:sid>", methods=["PATCH"])
def update_session(sid):
    status=(request.json or {}).get("status")
    if status not in {"Planned","Done","Skipped"}: return json_error("Invalid status")
    execute("UPDATE study_sessions SET status=%s WHERE session_id=%s",(status,sid)); return jsonify({"ok":True})


@app.get("/api/plan")
def plan_preview():
    days=max(1,min(14,int(request.args.get("days",7))))
    scheduled,remaining,meta=build_plan(days)
    return jsonify({"sessions":[{**x,"starts_at":iso(x["starts_at"]),"ends_at":iso(x["ends_at"])} for x in scheduled],"remaining":remaining,"meta":meta})


@app.post("/api/plan/generate")
def generate_plan():
    days=max(1,min(14,int((request.json or {}).get("days",7))))
    start=date.today(); end=start+timedelta(days=days)
    # Clear the generated horizon before calculating availability so old plan
    # rows cannot block or duplicate the newly generated schedule.
    execute("DELETE FROM study_sessions WHERE status='Planned' AND starts_at >= %s AND starts_at < %s",(datetime.combine(start,time.min),datetime.combine(end,time.min)))
    scheduled,remaining,meta=build_plan(days)
    if not scheduled:return jsonify({"created":0,"sessions":[],"remaining":remaining,"meta":meta})
    created=[]
    for s in scheduled:
        sid=execute("INSERT INTO study_sessions(title,topic_id,starts_at,ends_at,status) VALUES(%s,%s,%s,%s,'Planned')",(f"Study · {s['title']}",s['topic_id'],s['starts_at'],s['ends_at']))
        created.append({"id":sid,**{k:(iso(v) if isinstance(v,(datetime,date)) else v) for k,v in s.items()}})
    return jsonify({"created":len(created),"sessions":created,"remaining":remaining,"meta":meta})


@app.post("/api/revision/preview")
def revision_preview():
    d=request.json or {}; method=d.get("method","fibonacci"); days=max(1,min(60,int(d.get("days",30))))
    rows=fetch_all("SELECT t.topic_id,t.name,s.name FROM topics t JOIN subjects s ON s.subject_id=t.subject_id WHERE t.status='Completed' ORDER BY t.topic_id")
    topics=[{"name":r[1],"subject":r[2],"id":r[0]} for r in rows]
    schedule=generate_review_schedule(date.today(),topics,method)
    schedule=[x for x in schedule if x["date"] <= date.today()+timedelta(days=days)]
    return jsonify([{**x,"date":x["date"].isoformat()} for x in schedule])


@app.get("/api/checkin")
def get_checkin():
    row=fetch_all("SELECT check_date,available_minutes,changes_note,reflection FROM daily_checkins WHERE check_date=%s",(date.today(),))
    return jsonify({"date":date.today().isoformat(),"available_minutes":row[0][1],"changes_note":row[0][2],"reflection":row[0][3]} if row else {"date":date.today().isoformat(),"available_minutes":0,"changes_note":"","reflection":""})


@app.post("/api/checkin")
def save_checkin():
    d=request.json or {}; execute("INSERT INTO daily_checkins(check_date,available_minutes,changes_note,reflection) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE available_minutes=VALUES(available_minutes),changes_note=VALUES(changes_note),reflection=VALUES(reflection)",(date.today(),int(d.get("available_minutes",0)),d.get("changes_note",""),d.get("reflection","")))
    return jsonify({"ok":True})


@app.get("/api/week.csv")
def week_csv():
    start=date.today()-timedelta(days=date.today().weekday()); end=start+timedelta(days=6)
    rows=fetch_all("SELECT title,'Study' AS kind,starts_at,ends_at FROM study_sessions WHERE DATE(starts_at) BETWEEN %s AND %s UNION ALL SELECT title,category,starts_at,ends_at FROM events WHERE DATE(starts_at) BETWEEN %s AND %s ORDER BY starts_at",(start,end,start,end))
    out=StringIO(); w=csv.writer(out); w.writerow(["Date","Day","Start","End","Activity","Type"])
    for title,kind,a,b in rows:w.writerow([a.date().isoformat(),a.strftime('%A'),a.strftime('%H:%M'),b.strftime('%H:%M'),title,kind])
    return send_file(BytesIO(out.getvalue().encode()),mimetype="text/csv",as_attachment=True,download_name="studyos_week.csv")


@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"error":str(e)}),500





@app.route("/api/topics/<int:tid>", methods=["DELETE"])
def delete_topic(tid):
    execute("DELETE FROM topics WHERE topic_id=%s", (tid,))
    return jsonify({"ok": True})


@app.route("/api/tasks/<int:tid>", methods=["DELETE"])
def delete_task(tid):
    execute("DELETE FROM tasks WHERE task_id=%s", (tid,))
    return jsonify({"ok": True})


@app.route("/api/tasks/full/<int:tid>", methods=["PATCH"])
def update_task_full(tid):
    d = request.json or {}
    fields = []
    vals = []
    for key, col in [("title", "title"), ("subject_id", "subject_id"), ("priority", "priority"), ("status", "status"), ("notes", "notes")]:
        if key in d:
            fields.append(f"{col}=%s")
            vals.append(d[key] if d[key] != "" else None)
    if "due_at" in d:
        fields.append("due_at=%s")
        vals.append(parse_dt(d["due_at"]) if d["due_at"] else None)
    if not fields:
        return json_error("Nothing to update")
    vals.append(tid)
    execute(f"UPDATE tasks SET {','.join(fields)} WHERE task_id=%s", tuple(vals))
    return jsonify({"ok": True})


@app.route("/api/exams/<int:eid>", methods=["DELETE"])
def delete_exam(eid):
    execute("DELETE FROM exams WHERE exam_id=%s", (eid,))
    return jsonify({"ok": True})


@app.route("/api/exams/<int:eid>", methods=["PATCH"])
def update_exam(eid):
    d = request.json or {}
    fields = []
    vals = []
    for key, col in [("title", "title"), ("subject_id", "subject_id"), ("location", "location"), ("notes", "notes")]:
        if key in d:
            fields.append(f"{col}=%s")
            vals.append(d[key] if d[key] != "" else None)
    if "starts_at" in d:
        fields.append("starts_at=%s")
        vals.append(parse_dt(d["starts_at"]))
    if not fields:
        return json_error("Nothing to update")
    vals.append(eid)
    execute(f"UPDATE exams SET {','.join(fields)} WHERE exam_id=%s", tuple(vals))
    return jsonify({"ok": True})


@app.route("/api/routine/<int:rid>", methods=["DELETE"])
def delete_routine(rid):
    execute("DELETE FROM routine_blocks WHERE routine_id=%s", (rid,))
    return jsonify({"ok": True})


@app.route("/api/routine/<int:rid>", methods=["PATCH"])
def update_routine(rid):
    d = request.json or {}
    fields = []
    vals = []
    if "category" in d and d["category"] not in ROUTINE_CATEGORIES:
        return json_error("Invalid routine category. Choose from: " + ", ".join(sorted(ROUTINE_CATEGORIES)))
    if "weekday" in d:
        try: weekday=int(d["weekday"])
        except (TypeError,ValueError): return json_error("Weekday must be between 0 and 6")
        if weekday not in range(7): return json_error("Weekday must be between 0 and 6")
    existing=fetch_all("SELECT starts_at,ends_at FROM routine_blocks WHERE routine_id=%s", (rid,))
    if not existing: return json_error("Routine block not found",404)
    start=d.get("starts_at",existing[0][0]); end=d.get("ends_at",existing[0][1])
    if end <= start: return json_error("End time must be after start time")
    for key, col in [("title", "title"), ("category", "category")]:
        if key in d:
            fields.append(f"{col}=%s"); vals.append(d[key])
    if "weekday" in d: fields.append("weekday=%s"); vals.append(weekday)
    if "starts_at" in d: fields.append("starts_at=%s"); vals.append(start)
    if "ends_at" in d: fields.append("ends_at=%s"); vals.append(end)
    if not fields: return json_error("Nothing to update")
    vals.append(rid)
    execute(f"UPDATE routine_blocks SET {','.join(fields)} WHERE routine_id=%s", tuple(vals))
    return jsonify({"ok": True})


@app.route("/api/events/<int:eid>", methods=["DELETE"])
def delete_event(eid):
    execute("DELETE FROM events WHERE event_id=%s", (eid,))
    return jsonify({"ok": True})


@app.route("/api/events/<int:eid>", methods=["PATCH"])
def update_event(eid):
    d = request.json or {}
    fields = []
    vals = []
    if "category" in d and d["category"] not in EVENT_CATEGORIES:
        return json_error("Invalid event category. Choose from: " + ", ".join(sorted(EVENT_CATEGORIES)))
    for key, col in [("title", "title"), ("category", "category"), ("location", "location"), ("notes", "notes")]:
        if key in d:
            fields.append(f"{col}=%s")
            vals.append(d[key])
    if "starts_at" in d or "ends_at" in d:
        existing=fetch_all("SELECT starts_at,ends_at FROM events WHERE event_id=%s", (eid,))
        if not existing: return json_error("Event not found",404)
        starts=parse_dt(d["starts_at"]) if "starts_at" in d else existing[0][0]
        ends=parse_dt(d["ends_at"]) if "ends_at" in d else existing[0][1]
        if not starts or not ends or ends <= starts: return json_error("Event end must be after its start")
        if "starts_at" in d: fields.append("starts_at=%s"); vals.append(starts)
        if "ends_at" in d: fields.append("ends_at=%s"); vals.append(ends)
    if not fields:
        return json_error("Nothing to update")
    vals.append(eid)
    execute(f"UPDATE events SET {','.join(fields)} WHERE event_id=%s", tuple(vals))
    return jsonify({"ok": True})


@app.route("/api/sessions/<int:sid>", methods=["DELETE"])
def delete_session(sid):
    execute("DELETE FROM study_sessions WHERE session_id=%s", (sid,))
    return jsonify({"ok": True})


@app.route("/api/sessions/full/<int:sid>", methods=["PATCH"])
def update_session_full(sid):
    d = request.json or {}
    fields = []
    vals = []
    for key, col in [("title", "title"), ("topic_id", "topic_id"), ("task_id", "task_id"), ("status", "status")]:
        if key in d:
            if key == "status" and d[key] not in SESSION_STATUSES:
                return json_error("Invalid session status")
            fields.append(f"{col}=%s")
            vals.append(d[key] if d[key] != "" else None)
    starts = parse_dt(d["starts_at"]) if "starts_at" in d else None
    ends = parse_dt(d["ends_at"]) if "ends_at" in d else None
    if "starts_at" in d or "ends_at" in d:
        existing = fetch_all("SELECT starts_at,ends_at FROM study_sessions WHERE session_id=%s", (sid,))
        if not existing:
            return json_error("Study session not found", 404)
        starts = starts or existing[0][0]
        ends = ends or existing[0][1]
        if not starts or not ends or ends <= starts:
            return json_error("Session end must be after its start")
        if "starts_at" in d: fields.append("starts_at=%s"); vals.append(starts)
        if "ends_at" in d: fields.append("ends_at=%s"); vals.append(ends)
    if not fields:
        return json_error("Nothing to update")
    vals.append(sid)
    execute(f"UPDATE study_sessions SET {','.join(fields)} WHERE session_id=%s", tuple(vals))
    return jsonify({"ok": True})


@app.route("/api/topics/full/<int:tid>", methods=["PATCH"])
def update_topic_full(tid):
    d = request.json or {}
    fields = []
    vals = []
    for key, col in [("name", "name"), ("minutes", "estimated_minutes"), ("status", "status")]:
        if key in d:
            fields.append(f"{col}=%s")
            vals.append(d[key])
    if not fields:
        return json_error("Nothing to update")
    vals.append(tid)
    execute(f"UPDATE topics SET {','.join(fields)} WHERE topic_id=%s", tuple(vals))
    return jsonify({"ok": True})
if __name__ == "__main__":
    app.run(host="127.0.0.1",port=5000,debug=True)
