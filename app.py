import streamlit as st
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import certifi
import math
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit.components.v1 as components

# MongoDB Atlas connection with SSL certificate
try:
    client = MongoClient(
        "mongodb+srv://piyushsh:OSfe9TjB63NVg2ix@aistudyplanner.2w7djdq.mongodb.net/",
        tlsCAFile=certifi.where()
    )
    client.admin.command("ping")
    db = client["study_planner"]
    collection = db["user_inputs"]
    plans_collection = db["study_plans"]
    tasks_collection = db["tasks"]
    logs_collection = db["productivity_logs"]
    db_connected = True
except Exception as e:
    db_connected = False
    db_error = str(e)

# Page config
st.set_page_config(page_title="AI Study Planner", page_icon="📚", layout="wide")

if not db_connected:
    st.error(f"❌ MongoDB connection failed: {db_error}")
    st.stop()

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    /* Global */
    .block-container { padding-top: 1rem; }

    /* Header */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0; font-size: 2rem; font-weight: 700;
    }
    .main-header p {
        margin: 0.3rem 0 0 0; font-size: 1rem; opacity: 0.9;
    }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.2rem;
        border-radius: 14px;
        text-align: center;
        color: white;
        border: 1px solid rgba(255,255,255,0.08);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-3px); }
    .metric-card .metric-icon { font-size: 2rem; margin-bottom: 0.3rem; }
    .metric-card .metric-value { font-size: 1.8rem; font-weight: 700; }
    .metric-card .metric-label { font-size: 0.85rem; opacity: 0.7; margin-top: 0.2rem; }

    /* Day Card */
    .day-card {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
        padding: 1.2rem 1.5rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        color: white;
    }
    .day-card h4 { margin: 0 0 0.8rem 0; color: #667eea; font-size: 1.1rem; }
    .day-card .task-item {
        padding: 0.4rem 0;
        font-size: 0.95rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .day-card .task-item:last-child { border-bottom: none; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }
    [data-testid="stSidebar"] .stMarkdown { color: white; }

    /* Nav Button */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.8rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.4rem;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.2s;
        color: white;
        text-decoration: none;
    }
    .nav-item:hover { background: rgba(102,126,234,0.2); }
    .nav-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    .nav-item .nav-icon { font-size: 1.3rem; }

    /* Section Title */
    .section-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* Task Row */
    .task-row {
        background: rgba(26,26,46,0.5);
        padding: 0.8rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* Status Badge */
    .badge-done {
        background: #22c55e; color: white; padding: 0.2rem 0.7rem;
        border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }
    .badge-pending {
        background: #f59e0b; color: white; padding: 0.2rem 0.7rem;
        border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }

    /* Danger zone */
    .danger-zone {
        background: rgba(255, 77, 77, 0.08);
        border: 1px solid rgba(255, 77, 77, 0.3);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-top: 1rem;
    }
    .danger-zone-title {
        color: #ff4d4d;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
    }

    /* Hide default Streamlit elements */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ===================== HELPER: SEND BROWSER NOTIFICATION =====================
def send_browser_notification(title, body, tag="study-notify"):
    js_code = f"""
    <script>
    (function() {{
        if (!("Notification" in window)) return;
        function fireNotification() {{
            var n = new Notification("{title}", {{
                body: "{body}",
                icon: "https://cdn-icons-png.flaticon.com/512/2232/2232688.png",
                tag: "{tag}",
                requireInteraction: false
            }});
            n.onclick = function() {{ window.focus(); n.close(); }};
            setTimeout(function() {{ n.close(); }}, 6000);
        }}
        if (Notification.permission === "granted") {{
            fireNotification();
        }} else if (Notification.permission !== "denied") {{
            Notification.requestPermission().then(function(p) {{
                if (p === "granted") fireNotification();
            }});
        }}
    }})();
    </script>
    """
    components.html(js_code, height=0)


# ===================== HELPER: METRIC CARD =====================
def metric_card(icon, value, label):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)


# ===================== SCHEDULE GENERATOR FUNCTION =====================
def generate_schedule(user_data):
    subjects = user_data["subjects"]
    total_days = user_data["study_days"]
    daily_hours = user_data["daily_hours"]

    all_topics = []
    for sub in subjects:
        if sub["topics"]:
            for topic in sub["topics"]:
                all_topics.append({"subject": sub["subject"], "topic": topic})
        else:
            all_topics.append({"subject": sub["subject"], "topic": "General Study"})

    total_topics = len(all_topics)
    if total_topics == 0:
        return []

    total_available_hours = daily_hours * total_days
    hours_per_topic = max(0.5, math.floor((total_available_hours / total_topics) * 2) / 2)
    hours_per_topic = min(hours_per_topic, daily_hours)

    schedule = []
    topic_index = 0

    for day in range(1, total_days + 1):
        day_tasks = []
        remaining_hours = daily_hours

        while remaining_hours >= 0.5 and topic_index < total_topics:
            duration = min(hours_per_topic, remaining_hours)
            day_tasks.append({
                "subject": all_topics[topic_index]["subject"],
                "topic": all_topics[topic_index]["topic"],
                "duration": duration
            })
            remaining_hours -= duration
            topic_index += 1

        if remaining_hours >= 0.5 and day_tasks:
            day_tasks.append({
                "subject": "Revision",
                "topic": "Review previous topics",
                "duration": remaining_hours
            })

        if topic_index >= total_topics and not day_tasks:
            day_tasks.append({
                "subject": "Revision",
                "topic": "Review all subjects",
                "duration": daily_hours
            })

        schedule.append({"day": day, "tasks": day_tasks})

    return schedule


# ===================== SIDEBAR NAVIGATION =====================
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-size: 3rem;">📚</div>
        <div style="font-size: 1.2rem; font-weight: 700; color: #667eea; margin-top: 0.3rem;">
            AI Study Planner
        </div>
        <div style="font-size: 0.8rem; color: #aaa; margin-top: 0.2rem;">
            Boost Your Productivity
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Fetch user info for sidebar
    sidebar_user = collection.find_one(sort=[("created_at", -1)])
    if sidebar_user:
        user_name_sidebar = sidebar_user["name"]
        total_t = tasks_collection.count_documents({"user_name": user_name_sidebar})
        done_t = tasks_collection.count_documents({"user_name": user_name_sidebar, "status": "completed"})
        pend_t = total_t - done_t

        st.markdown(f"""
        <div style="background: rgba(102,126,234,0.1); padding: 0.8rem; border-radius: 10px; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; color: #aaa;">👤 Student</div>
            <div style="font-size: 1rem; font-weight: 600; color: white;">{sidebar_user['name']}</div>
            <div style="font-size: 0.8rem; color: #aaa; margin-top: 0.3rem;">🎯 Daily Goal: {sidebar_user['daily_hours']} hrs/day</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        total_t = 0
        done_t = 0
        pend_t = 0

    st.markdown("---")

    # Navigation
    nav_options = {
        "📝 Input Details": "input",
        "📅 Study Planner": "planner",
        "✅ Tasks": "tasks",
        "⏱️ Focus Timer": "timer",
        "📊 Productivity Log": "log",
        "📈 Dashboard": "dashboard",
        "🗂️ Manage Data": "manage"
    }

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "input"

    for label, key in nav_options.items():
        is_active = st.session_state["current_page"] == key
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                      type="primary" if is_active else "secondary"):
            st.session_state["current_page"] = key
            st.rerun()

    st.markdown("---")

    # Quick Stats in Sidebar
    if sidebar_user:
        st.markdown(f"""
        <div style="padding: 0.5rem 0;">
            <div style="font-size: 0.85rem; font-weight: 600; color: #667eea; margin-bottom: 0.5rem;">📊 Quick Stats</div>
            <div style="color: white; font-size: 0.85rem;">✅ Completed: {done_t}</div>
            <div style="color: white; font-size: 0.85rem;">⏳ Pending: {pend_t}</div>
            <div style="color: white; font-size: 0.85rem;">📋 Total: {total_t}</div>
        </div>
        """, unsafe_allow_html=True)


# ===================== NOTIFICATIONS ON LOAD =====================
def check_and_notify_pending_tasks():
    # Only notify once per session
    if st.session_state.get("_notified_pending", False):
        return
    
    latest_user = collection.find_one(sort=[("created_at", -1)])
    if not latest_user:
        return
    user_name = latest_user["name"]
    pending_count = tasks_collection.count_documents({"user_name": user_name, "status": "pending"})
    if pending_count > 0:
        pending_tasks = list(tasks_collection.find(
            {"user_name": user_name, "status": "pending"}).limit(3))
        task_lines = [f"\\u2022 {t['subject']} - {t['topic']}" for t in pending_tasks]
        preview_text = "\\n".join(task_lines)
        if pending_count > 3:
            preview_text += f"\\n...and {pending_count - 3} more"
        msg = f"You have {pending_count} pending task(s) today!\\n{preview_text}\\nStay focused!"
        send_browser_notification("📚 AI Study Planner Reminder", msg, "pending-tasks")
        st.toast(f"🔔 You have {pending_count} pending task(s)! Stay focused!", icon="📚")
    
    st.session_state["_notified_pending"] = True


def check_inactivity_reminder():
    # Only notify once per session
    if st.session_state.get("_notified_inactivity", False):
        return
    
    latest_user = collection.find_one(sort=[("created_at", -1)])
    if not latest_user:
        return
    user_name = latest_user["name"]
    latest_log = logs_collection.find_one({"user_name": user_name}, sort=[("logged_at", -1)])
    if not latest_log:
        send_browser_notification("📚 Study Reminder",
                                  "You havent logged any study sessions yet. Time to start!", "inactivity-reminder")
        st.toast("⏰ No study sessions found. Time to start studying!", icon="📚")
        st.session_state["_notified_inactivity"] = True
        return
    if "logged_at" in latest_log and latest_log["logged_at"]:
        hours_since = (datetime.now() - latest_log["logged_at"]).total_seconds() / 3600
        if hours_since >= 3:
            send_browser_notification("⏰ Inactive Study Reminder",
                                      f"You havent studied for {hours_since:.1f} hours. Time to focus!",
                                      "inactivity-reminder")
            st.toast(f"⏰ You haven't studied for {hours_since:.1f} hours. Time to focus!", icon="⏰")
    
    st.session_state["_notified_inactivity"] = True


check_and_notify_pending_tasks()
check_inactivity_reminder()


# ===================== HEADER =====================
latest_user_header = collection.find_one(sort=[("created_at", -1)])
header_name = latest_user_header["name"] if latest_user_header else "Student"
header_goal = f"{latest_user_header['daily_hours']} hrs/day" if latest_user_header else "—"

st.markdown(f"""
<div class="main-header">
    <h1>📚 AI Study Planner – Boost Your Productivity</h1>
    <p>👤 {header_name} &nbsp;|&nbsp; 🎯 Daily Goal: {header_goal} &nbsp;|&nbsp; 📅 {datetime.now().strftime('%A, %B %d, %Y')}</p>
</div>
""", unsafe_allow_html=True)


# ===================== PAGE: INPUT DETAILS =====================
if st.session_state["current_page"] == "input":
    st.markdown('<div class="section-title">📝 Student Details & Subject Input</div>', unsafe_allow_html=True)

    with st.container():
        name = st.text_input("👤 Student Name", placeholder="Enter your full name")

        num_subjects = st.number_input("📚 Number of Subjects", min_value=1, max_value=20, value=1, step=1)

        subjects_data = []
        for i in range(int(num_subjects)):
            with st.container():
                st.markdown(f"**📖 Subject {i + 1}**")
                col1, col2 = st.columns(2)
                with col1:
                    subject = st.text_input(f"Subject Name", key=f"subject_{i}",
                                            placeholder="e.g. Mathematics")
                with col2:
                    topics = st.text_input(f"Subtopics (comma separated)", key=f"topics_{i}",
                                           placeholder="e.g. Algebra, Calculus, Geometry")
                subjects_data.append({"subject": subject, "topics": topics})

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            daily_hours = st.number_input("⏱️ Daily Available Study Hours",
                                          min_value=0.5, max_value=24.0, value=4.0, step=0.5)
        with col2:
            study_days = st.number_input("📅 Number of Study Days",
                                         min_value=1, max_value=365, value=7, step=1)

        st.markdown("")

        if st.button("💾 Save Input & Continue", type="primary", use_container_width=True):
            if not name.strip():
                st.error("Please enter your name.")
            elif any(not s["subject"].strip() for s in subjects_data):
                st.error("Please fill in all subject names.")
            else:
                subjects_list = []
                for s in subjects_data:
                    topic_list = [t.strip() for t in s["topics"].split(",") if t.strip()]
                    subjects_list.append({"subject": s["subject"].strip(), "topics": topic_list})

                document = {
                    "name": name.strip(),
                    "subjects": subjects_list,
                    "daily_hours": daily_hours,
                    "study_days": int(study_days),
                    "created_at": datetime.now()
                }

                try:
                    collection.insert_one(document)
                    st.success("✅ Input saved successfully!")
                    with st.expander("📄 View Saved Data"):
                        st.json({
                            "name": document["name"],
                            "subjects": document["subjects"],
                            "daily_hours": document["daily_hours"],
                            "study_days": document["study_days"]
                        })
                except Exception as e:
                    st.error(f"❌ Failed to save data: {e}")


# ===================== PAGE: STUDY PLANNER =====================
elif st.session_state["current_page"] == "planner":
    st.markdown('<div class="section-title">📅 Study Schedule Generator</div>', unsafe_allow_html=True)

    latest_input = collection.find_one(sort=[("created_at", -1)])

    if not latest_input:
        st.warning("⚠️ No user input found. Please go to **Input Details** and save your data first.")
    else:
        # Info bar
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            metric_card("👤", latest_input["name"], "Student")
        with info_col2:
            metric_card("📚", str(len(latest_input["subjects"])), "Subjects")
        with info_col3:
            metric_card("📅", f"{latest_input['study_days']} days", "Study Period")

        st.markdown("")

        if st.button("🚀 Generate Study Plan", type="primary", use_container_width=True):
            schedule = generate_schedule(latest_input)

            if not schedule:
                st.error("❌ Could not generate schedule.")
            else:
                plan_document = {
                    "user_name": latest_input["name"],
                    "schedule": schedule,
                    "created_at": datetime.now()
                }

                try:
                    plans_collection.insert_one(plan_document)
                    tasks_collection.delete_many({"user_name": latest_input["name"]})

                    task_docs = []
                    for day_data in schedule:
                        for task in day_data["tasks"]:
                            task_docs.append({
                                "user_name": latest_input["name"],
                                "day": day_data["day"],
                                "subject": task["subject"],
                                "topic": task["topic"],
                                "duration": task["duration"],
                                "status": "pending",
                                "created_at": datetime.now()
                            })

                    if task_docs:
                        tasks_collection.insert_many(task_docs)

                    st.success("✅ Study plan generated and tasks created!")

                except Exception as e:
                    st.error(f"❌ Failed to save plan: {e}")

                st.session_state["generated_schedule"] = schedule
                st.session_state["plan_user"] = latest_input["name"]

        # Display schedule in day cards
        if "generated_schedule" in st.session_state:
            st.markdown("---")
            st.markdown(f'<div class="section-title">🗓️ Study Plan for {st.session_state["plan_user"]}</div>',
                        unsafe_allow_html=True)

            cols_per_row = 2
            schedule = st.session_state["generated_schedule"]
            for i in range(0, len(schedule), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(schedule):
                        day_data = schedule[idx]
                        tasks_html = ""
                        for task in day_data["tasks"]:
                            icon = "🔁" if task["subject"] == "Revision" else "📖"
                            h_label = "hr" if task["duration"] == 1 else "hrs"
                            tasks_html += f'<div class="task-item">{icon} <b>{task["subject"]}</b> – {task["topic"]} <span style="color:#667eea;">({task["duration"]} {h_label})</span></div>'

                        with col:
                            st.markdown(f"""
                            <div class="day-card">
                                <h4>🗓️ Day {day_data['day']}</h4>
                                {tasks_html}
                            </div>
                            """, unsafe_allow_html=True)

        # Previous plans
        st.markdown("---")
        st.markdown('<div class="section-title">📂 Previously Saved Plans</div>', unsafe_allow_html=True)
        saved_plans = list(plans_collection.find(sort=[("created_at", -1)]).limit(5))

        if not saved_plans:
            st.write("No saved plans yet.")
        else:
            for plan in saved_plans:
                with st.expander(f"📋 {plan['user_name']} — {plan['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    for day_data in plan["schedule"]:
                        st.markdown(f"**Day {day_data['day']}**")
                        for task in day_data["tasks"]:
                            st.write(f"- {task['subject']} – {task['topic']} ({task['duration']} hrs)")


# ===================== PAGE: TASKS =====================
elif st.session_state["current_page"] == "tasks":
    st.markdown('<div class="section-title">✅ Task Tracker</div>', unsafe_allow_html=True)

    latest_user = collection.find_one(sort=[("created_at", -1)])

    if not latest_user:
        st.warning("⚠️ No user found. Please save input first.")
    else:
        user_name = latest_user["name"]
        all_tasks = list(tasks_collection.find({"user_name": user_name}).sort("day", 1))

        if not all_tasks:
            st.warning("⚠️ No tasks found. Please generate a study plan first.")
        else:
            total_tasks = len(all_tasks)
            completed_tasks = len([t for t in all_tasks if t["status"] == "completed"])
            pending_tasks = total_tasks - completed_tasks
            progress = completed_tasks / total_tasks if total_tasks > 0 else 0
            score = round(progress * 100, 1)

            # Metric cards
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                metric_card("📋", str(total_tasks), "Total Tasks")
            with m2:
                metric_card("✅", str(completed_tasks), "Completed")
            with m3:
                metric_card("⏳", str(pending_tasks), "Pending")
            with m4:
                metric_card("🏆", f"{score}%", "Score")

            st.markdown("")
            st.progress(progress, text=f"Overall Progress: {int(progress * 100)}%")
            st.markdown("---")

            # Task list grouped by day
            days = sorted(set(t["day"] for t in all_tasks))

            for day in days:
                st.markdown(f"### 🗓️ Day {day}")
                day_tasks = [t for t in all_tasks if t["day"] == day]

                for task in day_tasks:
                    task_id = str(task["_id"])
                    is_completed = task["status"] == "completed"

                    col1, col2, col3, col4, col5 = st.columns([3, 3, 1.5, 1.5, 2])

                    with col1:
                        icon = "✅" if is_completed else ("🔁" if task["subject"] == "Revision" else "📖")
                        st.write(f"{icon} **{task['subject']}**")

                    with col2:
                        st.write(task["topic"])

                    with col3:
                        h_label = "hr" if task["duration"] == 1 else "hrs"
                        st.write(f"{task['duration']} {h_label}")

                    with col4:
                        if is_completed:
                            st.markdown('<span class="badge-done">Done</span>', unsafe_allow_html=True)
                        else:
                            st.markdown('<span class="badge-pending">Pending</span>', unsafe_allow_html=True)

                    with col5:
                        if not is_completed:
                            if st.button("✔ Complete", key=f"complete_{task_id}"):
                                tasks_collection.update_one(
                                    {"_id": ObjectId(task_id)},
                                    {"$set": {"status": "completed"}}
                                )
                                logs_collection.insert_one({
                                    "user_name": user_name,
                                    "subject": task["subject"],
                                    "topic": task["topic"],
                                    "hours_studied": task["duration"],
                                    "study_minutes": int(task["duration"] * 60),
                                    "date": datetime.now().strftime("%Y-%m-%d"),
                                    "logged_at": datetime.now()
                                })
                                st.rerun()
                        else:
                            st.write("—")

                st.markdown("---")


# ===================== PAGE: FOCUS TIMER =====================
elif st.session_state["current_page"] == "timer":
    st.markdown('<div class="section-title">⏱️ Focus Timer (Pomodoro)</div>', unsafe_allow_html=True)

    latest_user = collection.find_one(sort=[("created_at", -1)])

    if not latest_user:
        st.warning("⚠️ No user found. Please save input first.")
    else:
        user_name = latest_user["name"]

        # --- Today's Progress ---
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_logs = list(logs_collection.find({"user_name": user_name, "date": today_str}))

        latest_input = collection.find_one({"name": user_name}, sort=[("created_at", -1)])
        daily_goal_minutes = int(latest_input["daily_hours"] * 60) if latest_input else 240

        today_minutes = 0
        for log in today_logs:
            if "study_minutes" in log:
                today_minutes += log["study_minutes"]
            elif "hours_studied" in log:
                today_minutes += int(log["hours_studied"] * 60)

        daily_progress = min(today_minutes / daily_goal_minutes, 1.0) if daily_goal_minutes > 0 else 0
        remaining_minutes = max(daily_goal_minutes - today_minutes, 0)

        # Progress cards
        p1, p2, p3 = st.columns(3)
        with p1:
            metric_card("🎯", f"{daily_goal_minutes} min", "Daily Goal")
        with p2:
            metric_card("✅", f"{today_minutes} min", "Studied Today")
        with p3:
            metric_card("⏳", f"{remaining_minutes} min", "Remaining")

        st.markdown("")
        st.progress(daily_progress, text=f"Today's Study Progress: {int(daily_progress * 100)}%")

        if today_minutes >= daily_goal_minutes:
            st.success("🎉 Great job! You achieved today's study target!")
        else:
            st.info(f"📌 You still have **{remaining_minutes} minutes** to reach today's study goal.")

        st.markdown("---")

        # Timer settings
        st.markdown("### 🎯 Session Settings")
        s1, s2 = st.columns(2)
        with s1:
            focus_minutes = st.number_input("Focus Duration (min)", min_value=5, max_value=120,
                                            value=25, step=5, key="focus_duration")
        with s2:
            break_minutes = st.number_input("Break Duration (min)", min_value=1, max_value=30,
                                            value=5, step=1, key="break_duration")

        s3, s4 = st.columns(2)
        with s3:
            timer_subject = st.text_input("📚 Subject", key="timer_subject", placeholder="e.g. Mathematics")
        with s4:
            timer_topic = st.text_input("📖 Topic", key="timer_topic", placeholder="e.g. Algebra")

        st.markdown("---")
        st.markdown("### ⏱️ Pomodoro Timer")

        timer_html = f"""
        <div id="timer-container" style="
            text-align: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 30px;
            background: linear-gradient(135deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
            border-radius: 20px;
            color: white;
            max-width: 520px;
            margin: 0 auto;
            border: 1px solid rgba(102,126,234,0.3);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        ">
            <div id="timer-status" style="
                font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #667eea;
            ">Ready to Focus</div>

            <div id="timer-display" style="
                font-size: 90px; font-weight: 700; letter-spacing: 4px; margin: 20px 0;
                text-shadow: 0 0 30px rgba(102,126,234,0.5);
            ">{focus_minutes:02d}:00</div>

            <div id="timer-progress-bar" style="
                width: 80%; height: 10px; background: #333; border-radius: 5px;
                margin: 20px auto; overflow: hidden;
            ">
                <div id="timer-progress" style="
                    width: 0%; height: 100%;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    border-radius: 5px; transition: width 1s linear;
                "></div>
            </div>

            <div id="session-info" style="font-size: 14px; color: #aaa; margin-bottom: 20px;">
                Focus: {focus_minutes} min | Break: {break_minutes} min
            </div>

            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button id="startBtn" onclick="startTimer()" style="
                    padding: 12px 35px; font-size: 16px; font-weight: 600;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white; border: none; border-radius: 12px; cursor: pointer;
                ">▶ Start Focus</button>

                <button id="pauseBtn" onclick="pauseTimer()" style="
                    padding: 12px 35px; font-size: 16px; font-weight: 600;
                    background: linear-gradient(135deg, #f093fb, #f5576c);
                    color: white; border: none; border-radius: 12px; cursor: pointer; display: none;
                ">⏸ Pause</button>

                <button id="resumeBtn" onclick="resumeTimer()" style="
                    padding: 12px 35px; font-size: 16px; font-weight: 600;
                    background: linear-gradient(135deg, #43e97b, #38f9d7);
                    color: white; border: none; border-radius: 12px; cursor: pointer; display: none;
                ">▶ Resume</button>

                <button id="stopBtn" onclick="stopTimer()" style="
                    padding: 12px 35px; font-size: 16px; font-weight: 600;
                    background: linear-gradient(135deg, #ff4d4d, #cc0000);
                    color: white; border: none; border-radius: 12px; cursor: pointer; display: none;
                ">⏹ Stop</button>

                <button id="breakBtn" onclick="startBreak()" style="
                    padding: 12px 35px; font-size: 16px; font-weight: 600;
                    background: linear-gradient(135deg, #43e97b, #38f9d7);
                    color: white; border: none; border-radius: 12px; cursor: pointer; display: none;
                ">☕ Start Break</button>
            </div>

            <div id="completed-msg" style="margin-top: 15px; font-size: 16px; color: #43e97b; display: none;"></div>
        </div>

        <script>
        if ("Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {{
            Notification.requestPermission();
        }}

        var focusSeconds = {focus_minutes} * 60;
        var breakSeconds = {break_minutes} * 60;
        var totalFocusSeconds = focusSeconds;
        var totalBreakSeconds = breakSeconds;
        var remaining = focusSeconds;
        var interval = null;
        var isRunning = false;
        var isBreak = false;
        var halfwayNotified = false;

        function notify(title, body, tag) {{
            if ("Notification" in window && Notification.permission === "granted") {{
                var n = new Notification(title, {{
                    body: body,
                    icon: "https://cdn-icons-png.flaticon.com/512/2232/2232688.png",
                    tag: tag || "timer-notify"
                }});
                setTimeout(function() {{ n.close(); }}, 6000);
            }}
        }}

        function updateDisplay() {{
            var mins = Math.floor(remaining / 60);
            var secs = remaining % 60;
            document.getElementById("timer-display").textContent =
                String(mins).padStart(2, '0') + ":" + String(secs).padStart(2, '0');
            var total = isBreak ? totalBreakSeconds : totalFocusSeconds;
            var elapsed = total - remaining;
            var pct = (elapsed / total) * 100;
            document.getElementById("timer-progress").style.width = pct + "%";
            if (isBreak) {{
                document.getElementById("timer-progress").style.background = "linear-gradient(90deg, #43e97b, #38f9d7)";
            }} else {{
                document.getElementById("timer-progress").style.background = "linear-gradient(90deg, #667eea, #764ba2)";
            }}
        }}

        function tick() {{
            if (remaining <= 0) {{
                clearInterval(interval); interval = null; isRunning = false;
                if (isBreak) {{
                    document.getElementById("timer-status").textContent = "Break Over!";
                    document.getElementById("timer-status").style.color = "#667eea";
                    notify("☕ Break Over!", "Ready for the next study session?", "break-done");
                    document.getElementById("completed-msg").textContent = "Break complete! Start another session.";
                    document.getElementById("completed-msg").style.display = "block";
                    document.getElementById("breakBtn").style.display = "none";
                    document.getElementById("pauseBtn").style.display = "none";
                    document.getElementById("stopBtn").style.display = "none";
                    document.getElementById("startBtn").style.display = "inline-block";
                    isBreak = false; remaining = focusSeconds; updateDisplay();
                }} else {{
                    document.getElementById("timer-status").textContent = "Session Complete!";
                    document.getElementById("timer-status").style.color = "#43e97b";
                    notify("Focus Session Complete!", "Great work! Take a {break_minutes}-min break.", "focus-done");
                    document.getElementById("completed-msg").textContent = "Session complete! Take a {break_minutes}-min break.";
                    document.getElementById("completed-msg").style.display = "block";
                    document.getElementById("pauseBtn").style.display = "none";
                    document.getElementById("stopBtn").style.display = "none";
                    document.getElementById("startBtn").style.display = "none";
                    document.getElementById("breakBtn").style.display = "inline-block";
                }}
                return;
            }}
            remaining--;
            updateDisplay();
            if (!isBreak && !halfwayNotified && remaining <= Math.floor(totalFocusSeconds / 2)) {{
                halfwayNotified = true;
                notify("Halfway There!", "Stay focused. Keep going!", "halfway");
            }}
        }}

        function startTimer() {{
            if (isRunning) return;
            isRunning = true; isBreak = false; halfwayNotified = false; remaining = focusSeconds;
            document.getElementById("timer-status").textContent = "Focusing...";
            document.getElementById("timer-status").style.color = "#667eea";
            document.getElementById("completed-msg").style.display = "none";
            document.getElementById("startBtn").style.display = "none";
            document.getElementById("pauseBtn").style.display = "inline-block";
            document.getElementById("stopBtn").style.display = "inline-block";
            document.getElementById("breakBtn").style.display = "none";
            document.getElementById("resumeBtn").style.display = "none";
            notify("Focus Started", "Stay concentrated for {focus_minutes} minutes!", "focus-start");
            updateDisplay();
            interval = setInterval(tick, 1000);
        }}

        function pauseTimer() {{
            if (!isRunning) return;
            clearInterval(interval); interval = null; isRunning = false;
            document.getElementById("timer-status").textContent = isBreak ? "Break Paused" : "Focus Paused";
            document.getElementById("timer-status").style.color = "#f5576c";
            document.getElementById("pauseBtn").style.display = "none";
            document.getElementById("resumeBtn").style.display = "inline-block";
        }}

        function resumeTimer() {{
            if (isRunning) return;
            isRunning = true;
            document.getElementById("timer-status").textContent = isBreak ? "Break Time..." : "Focusing...";
            document.getElementById("timer-status").style.color = isBreak ? "#43e97b" : "#667eea";
            document.getElementById("resumeBtn").style.display = "none";
            document.getElementById("pauseBtn").style.display = "inline-block";
            interval = setInterval(tick, 1000);
        }}

        function stopTimer() {{
            clearInterval(interval); interval = null; isRunning = false;
            isBreak = false; halfwayNotified = false; remaining = focusSeconds;
            document.getElementById("timer-status").textContent = "Stopped";
            document.getElementById("timer-status").style.color = "#ff4d4d";
            document.getElementById("startBtn").style.display = "inline-block";
            document.getElementById("pauseBtn").style.display = "none";
            document.getElementById("stopBtn").style.display = "none";
            document.getElementById("resumeBtn").style.display = "none";
            document.getElementById("breakBtn").style.display = "none";
            document.getElementById("completed-msg").style.display = "none";
            document.getElementById("timer-progress").style.width = "0%";
            updateDisplay();
        }}

        function startBreak() {{
            isBreak = true; isRunning = true; remaining = breakSeconds;
            document.getElementById("timer-status").textContent = "Break Time...";
            document.getElementById("timer-status").style.color = "#43e97b";
            document.getElementById("completed-msg").style.display = "none";
            document.getElementById("breakBtn").style.display = "none";
            document.getElementById("pauseBtn").style.display = "inline-block";
            document.getElementById("stopBtn").style.display = "inline-block";
            document.getElementById("resumeBtn").style.display = "none";
            notify("Break Started", "Take a {break_minutes}-minute break!", "break-start");
            updateDisplay();
            interval = setInterval(tick, 1000);
        }}
        </script>
        """

        components.html(timer_html, height=450)

        st.markdown("---")

        # Log session
        st.markdown("### 📥 Log Completed Focus Session")

        if st.button("💾 Log This Focus Session", type="primary", use_container_width=True, key="log_focus"):
            subj = timer_subject.strip() if timer_subject.strip() else "General"
            top = timer_topic.strip() if timer_topic.strip() else "Focus Session"

            focus_log = {
                "user_name": user_name,
                "subject": subj,
                "topic": top,
                "hours_studied": round(focus_minutes / 60, 2),
                "study_minutes": focus_minutes,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "logged_at": datetime.now(),
                "source": "focus_timer"
            }

            try:
                logs_collection.insert_one(focus_log)
                st.success(f"✅ Logged: {subj} – {top} ({focus_minutes} min)")
                send_browser_notification("Session Logged!",
                                          f"{subj} - {top} ({focus_minutes} min) saved!", "session-logged")
            except Exception as e:
                st.error(f"❌ Failed: {e}")

        # Today's focus sessions
        st.markdown("---")
        st.markdown("### 📋 Today's Focus Sessions")

        today_focus = list(logs_collection.find({
            "user_name": user_name, "date": today_str, "source": "focus_timer"
        }).sort("logged_at", -1))

        if not today_focus:
            st.write("No focus sessions logged today.")
        else:
            focus_table = []
            for s in today_focus:
                focus_table.append({
                    "Subject": s["subject"],
                    "Topic": s["topic"],
                    "Minutes": s.get("study_minutes", int(s["hours_studied"] * 60)),
                    "Time": s["logged_at"].strftime("%H:%M")
                })
            st.table(pd.DataFrame(focus_table))

            total_focus_today = sum(f.get("study_minutes", 0) for f in today_focus)
            st.info(f"⏱️ Total focus today: **{total_focus_today} min** across **{len(today_focus)} session(s)**")


# ===================== PAGE: PRODUCTIVITY LOG =====================
elif st.session_state["current_page"] == "log":
    st.markdown('<div class="section-title">📊 Productivity Log</div>', unsafe_allow_html=True)

    latest_user = collection.find_one(sort=[("created_at", -1)])

    if not latest_user:
        st.warning("⚠️ No user found.")
    else:
        user_name = latest_user["name"]

        st.markdown("### 📝 Log a Study Session")

        with st.form("log_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                log_subject = st.text_input("📚 Subject", placeholder="e.g. Physics")
            with col2:
                log_topic = st.text_input("📖 Topic", placeholder="e.g. Thermodynamics")

            col3, col4 = st.columns(2)
            with col3:
                log_hours = st.number_input("⏱️ Hours Studied", min_value=0.5, max_value=24.0, value=1.0, step=0.5)
            with col4:
                log_date = st.date_input("📅 Date", value=datetime.now())

            submitted = st.form_submit_button("📥 Save Log", type="primary", use_container_width=True)

            if submitted:
                if not log_subject.strip():
                    st.error("Please enter a subject.")
                else:
                    log_doc = {
                        "user_name": user_name,
                        "subject": log_subject.strip(),
                        "topic": log_topic.strip() if log_topic.strip() else "General",
                        "hours_studied": log_hours,
                        "study_minutes": int(log_hours * 60),
                        "date": log_date.strftime("%Y-%m-%d"),
                        "logged_at": datetime.now()
                    }
                    try:
                        logs_collection.insert_one(log_doc)
                        st.success("✅ Study session logged!")
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")

        st.markdown("---")
        st.markdown("### 📋 Study History")

        all_logs = list(logs_collection.find({"user_name": user_name}).sort("logged_at", -1))

        if not all_logs:
            st.write("No study sessions logged yet.")
        else:
            total_hours = sum(log["hours_studied"] for log in all_logs)
            total_sessions = len(all_logs)
            unique_subjects = len(set(log["subject"] for log in all_logs))

            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("📚", str(total_sessions), "Total Sessions")
            with c2:
                metric_card("⏱️", f"{total_hours:.1f}", "Total Hours")
            with c3:
                metric_card("📖", str(unique_subjects), "Subjects Covered")

            st.markdown("---")

            log_table = []
            for log in all_logs:
                log_table.append({
                    "Date": log["date"],
                    "Subject": log["subject"],
                    "Topic": log["topic"],
                    "Hours": log["hours_studied"]
                })
            st.table(log_table)


# ===================== PAGE: DASHBOARD =====================
elif st.session_state["current_page"] == "dashboard":
    st.markdown('<div class="section-title">📈 Performance Analytics Dashboard</div>', unsafe_allow_html=True)

    latest_user = collection.find_one(sort=[("created_at", -1)])

    if not latest_user:
        st.warning("⚠️ No user found.")
    else:
        user_name = latest_user["name"]

        all_tasks = list(tasks_collection.find({"user_name": user_name}))
        all_logs = list(logs_collection.find({"user_name": user_name}))

        if not all_tasks:
            st.warning("⚠️ No tasks found. Generate a study plan first.")
        else:
            total_tasks = len(all_tasks)
            completed_tasks = len([t for t in all_tasks if t["status"] == "completed"])
            pending_tasks = total_tasks - completed_tasks
            total_study_hours = sum(log["hours_studied"] for log in all_logs) if all_logs else 0
            productivity_score = round((completed_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0

            # Metric cards
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                metric_card("📋", str(total_tasks), "Total Tasks")
            with m2:
                metric_card("✅", str(completed_tasks), "Completed")
            with m3:
                metric_card("⏳", str(pending_tasks), "Pending")
            with m4:
                metric_card("⏱️", f"{total_study_hours:.1f}h", "Study Hours")
            with m5:
                metric_card("🏆", f"{productivity_score}%", "Productivity")

            st.markdown("---")

            # Gauge
            st.markdown("### 🏆 Productivity Score")

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=productivity_score,
                title={"text": "Productivity Score (%)"},
                delta={"reference": 50, "increasing": {"color": "green"}, "decreasing": {"color": "red"}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#667eea"},
                    "steps": [
                        {"range": [0, 30], "color": "#ff4d4d"},
                        {"range": [30, 60], "color": "#ffa64d"},
                        {"range": [60, 80], "color": "#ffff4d"},
                        {"range": [80, 100], "color": "#4dff4d"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": productivity_score
                    }
                }
            ))
            fig_gauge.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Motivational message
            if productivity_score >= 80:
                st.success("🎉 Amazing work! You're crushing your study goals!")
            elif productivity_score >= 60:
                st.info("👍 Great job! You're on track. Stay consistent!")
            elif productivity_score >= 30:
                st.warning("⚡ You have pending tasks. Try to catch up!")
            else:
                st.error("🚨 You're falling behind. Focus on completing your tasks!")

            st.markdown("---")

            # Charts
            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                st.markdown("### 📊 Task Status")
                status_df = pd.DataFrame({
                    "Status": ["Completed", "Pending"],
                    "Count": [completed_tasks, pending_tasks]
                })
                fig_pie = px.pie(status_df, values="Count", names="Status", color="Status",
                                 color_discrete_map={"Completed": "#4dff4d", "Pending": "#ff4d4d"}, hole=0.4)
                fig_pie.update_traces(textposition="inside", textinfo="percent+label+value")
                fig_pie.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_pie, use_container_width=True)

            with chart_col2:
                st.markdown("### 📚 Hours by Subject")
                if all_logs:
                    subject_hours = {}
                    for log in all_logs:
                        subject_hours[log["subject"]] = subject_hours.get(log["subject"], 0) + log["hours_studied"]

                    hours_df = pd.DataFrame({
                        "Subject": list(subject_hours.keys()),
                        "Hours": list(subject_hours.values())
                    }).sort_values("Hours", ascending=True)

                    fig_bar = px.bar(hours_df, x="Hours", y="Subject", orientation="h",
                                     color="Hours", color_continuous_scale="Purples", text="Hours")
                    fig_bar.update_traces(texttemplate="%{text:.1f}h", textposition="outside")
                    fig_bar.update_layout(height=400, showlegend=False,
                                          paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.write("No study sessions logged yet.")

            st.markdown("---")

            # Daily progress stacked bar
            st.markdown("### 📅 Daily Task Progress")
            day_completed = {}
            day_pending = {}
            for task in all_tasks:
                d = task["day"]
                if task["status"] == "completed":
                    day_completed[d] = day_completed.get(d, 0) + 1
                else:
                    day_pending[d] = day_pending.get(d, 0) + 1

            all_days = sorted(set(t["day"] for t in all_tasks))
            fig_stacked = go.Figure()
            fig_stacked.add_trace(go.Bar(name="Completed",
                                         x=[f"Day {d}" for d in all_days],
                                         y=[day_completed.get(d, 0) for d in all_days],
                                         marker_color="#4dff4d"))
            fig_stacked.add_trace(go.Bar(name="Pending",
                                         x=[f"Day {d}" for d in all_days],
                                         y=[day_pending.get(d, 0) for d in all_days],
                                         marker_color="#ff4d4d"))
            fig_stacked.update_layout(barmode="stack", height=400,
                                       paper_bgcolor="rgba(0,0,0,0)", font_color="white",
                                       xaxis_title="Day", yaxis_title="Tasks")
            st.plotly_chart(fig_stacked, use_container_width=True)

            st.markdown("---")

            # Timeline
            if all_logs:
                st.markdown("### 📈 Study Hours Over Time")
                date_hours = {}
                for log in all_logs:
                    date_hours[log["date"]] = date_hours.get(log["date"], 0) + log["hours_studied"]

                sorted_dates = sorted(date_hours.keys())
                timeline_df = pd.DataFrame({
                    "Date": sorted_dates,
                    "Hours": [date_hours[d] for d in sorted_dates]
                })

                fig_line = px.line(timeline_df, x="Date", y="Hours", markers=True)
                fig_line.update_traces(line_color="#667eea", marker_size=10)
                fig_line.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_line, use_container_width=True)

                st.markdown("---")

            # Subject completion table
            st.markdown("### 📋 Subject-wise Completion")
            subject_stats = {}
            for task in all_tasks:
                subj = task["subject"]
                if subj not in subject_stats:
                    subject_stats[subj] = {"total": 0, "completed": 0}
                subject_stats[subj]["total"] += 1
                if task["status"] == "completed":
                    subject_stats[subj]["completed"] += 1

            subj_table = []
            for subj, stats in subject_stats.items():
                pct = round((stats["completed"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0
                subj_table.append({
                    "Subject": subj,
                    "Total": stats["total"],
                    "Done": stats["completed"],
                    "Pending": stats["total"] - stats["completed"],
                    "Progress": f"{pct}%"
                })
            st.table(pd.DataFrame(subj_table))


# ===================== PAGE: MANAGE DATA =====================
elif st.session_state["current_page"] == "manage":
    st.markdown('<div class="section-title">🗂️ Manage Study Data</div>', unsafe_allow_html=True)

    latest_user = collection.find_one(sort=[("created_at", -1)])

    if not latest_user:
        st.warning("⚠️ No user found. Please save input first.")
    else:
        user_name = latest_user["name"]

        # ---- Section 1: Study Plans ----
        st.markdown("### 📅 Your Study Plans")

        all_plans = list(plans_collection.find({"user_name": user_name}).sort("created_at", -1))

        if not all_plans:
            st.info("No study plans found.")
        else:
            for idx, plan in enumerate(all_plans):
                plan_id = str(plan["_id"])
                num_days = len(plan.get("schedule", []))
                created = plan["created_at"].strftime("%Y-%m-%d %H:%M")

                with st.container():
                    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])

                    with col1:
                        st.write(f"📋 **{plan['user_name']}** — Plan #{idx + 1}")
                    with col2:
                        st.write(f"📅 {num_days} days")
                    with col3:
                        st.write(f"🕐 {created}")
                    with col4:
                        confirm_key = f"confirm_del_plan_{plan_id}"
                        if confirm_key not in st.session_state:
                            st.session_state[confirm_key] = False

                        if not st.session_state[confirm_key]:
                            if st.button("🗑️ Delete", key=f"del_plan_{plan_id}", type="secondary"):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            st.warning("Are you sure?")
                            c_yes, c_no = st.columns(2)
                            with c_yes:
                                if st.button("✅ Yes", key=f"yes_plan_{plan_id}"):
                                    plans_collection.delete_one({"_id": ObjectId(plan_id)})
                                    st.session_state[confirm_key] = False
                                    st.success("✅ Study plan deleted successfully.")
                                    st.rerun()
                            with c_no:
                                if st.button("❌ No", key=f"no_plan_{plan_id}"):
                                    st.session_state[confirm_key] = False
                                    st.rerun()

                st.markdown("---")

        # ---- Section 2: Edit / Modify Tasks ----
        st.markdown("### ✏️ Edit / Modify Tasks")

        all_tasks = list(tasks_collection.find({"user_name": user_name}).sort("day", 1))

        if not all_tasks:
            st.info("No tasks found.")
        else:
            days = sorted(set(t["day"] for t in all_tasks))

            for day in days:
                day_tasks = [t for t in all_tasks if t["day"] == day]

                with st.expander(f"🗓️ Day {day} — {len(day_tasks)} task(s)", expanded=False):
                    for task in day_tasks:
                        task_id = str(task["_id"])

                        with st.form(key=f"edit_form_{task_id}"):
                            st.markdown(f"**Task ID:** `{task_id[:8]}...` | **Status:** {task['status']}")

                            e_col1, e_col2, e_col3 = st.columns([3, 3, 2])
                            with e_col1:
                                new_subject = st.text_input("Subject", value=task["subject"],
                                                            key=f"edit_subj_{task_id}")
                            with e_col2:
                                new_topic = st.text_input("Topic", value=task["topic"],
                                                          key=f"edit_topic_{task_id}")
                            with e_col3:
                                new_duration = st.number_input("Duration (hrs)",
                                                               value=float(task["duration"]),
                                                               min_value=0.5, max_value=12.0, step=0.5,
                                                               key=f"edit_dur_{task_id}")

                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                save_clicked = st.form_submit_button("💾 Save Changes", type="primary",
                                                                      use_container_width=True)
                            with btn_col2:
                                delete_clicked = st.form_submit_button("🗑️ Delete Task",
                                                                        use_container_width=True)

                            if save_clicked:
                                tasks_collection.update_one(
                                    {"_id": ObjectId(task_id)},
                                    {"$set": {
                                        "subject": new_subject.strip(),
                                        "topic": new_topic.strip(),
                                        "duration": new_duration
                                    }}
                                )
                                st.success(f"✅ Task updated: {new_subject} – {new_topic}")
                                st.rerun()

                            if delete_clicked:
                                tasks_collection.delete_one({"_id": ObjectId(task_id)})
                                st.success("✅ Task deleted successfully.")
                                st.rerun()

                        st.markdown("")

                    # ---- Add New Task for this Day ----
                    st.markdown("---")
                    st.markdown("**➕ Add a New Task to This Day**")

                    with st.form(key=f"add_task_form_day_{day}"):
                        a_col1, a_col2, a_col3 = st.columns([3, 3, 2])
                        with a_col1:
                            add_subject = st.text_input("Subject", key=f"add_subj_day_{day}",
                                                        placeholder="e.g. Mathematics")
                        with a_col2:
                            add_topic = st.text_input("Topic", key=f"add_topic_day_{day}",
                                                      placeholder="e.g. Algebra")
                        with a_col3:
                            add_duration = st.number_input("Duration (hrs)", min_value=0.5,
                                                           max_value=12.0, value=1.0, step=0.5,
                                                           key=f"add_dur_day_{day}")

                        add_clicked = st.form_submit_button("➕ Add Task", type="primary",
                                                             use_container_width=True)

                        if add_clicked:
                            if not add_subject.strip():
                                st.error("Please enter a subject name.")
                            else:
                                new_task_doc = {
                                    "user_name": user_name,
                                    "day": day,
                                    "subject": add_subject.strip(),
                                    "topic": add_topic.strip() if add_topic.strip() else "General Study",
                                    "duration": add_duration,
                                    "status": "pending",
                                    "created_at": datetime.now()
                                }
                                try:
                                    tasks_collection.insert_one(new_task_doc)
                                    st.success(f"✅ New task added: {add_subject.strip()} – Day {day}")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Failed to add task: {e}")

        # ---- Add Task to a New Day ----
        st.markdown("---")
        st.markdown("### ➕ Add Task to a New Day")

        with st.form(key="add_task_new_day_form"):
            nd_col1, nd_col2 = st.columns(2)
            with nd_col1:
                new_day_subject = st.text_input("Subject", key="new_day_subj",
                                                placeholder="e.g. Physics")
            with nd_col2:
                new_day_topic = st.text_input("Topic", key="new_day_topic",
                                              placeholder="e.g. Thermodynamics")

            nd_col3, nd_col4 = st.columns(2)
            with nd_col3:
                # Get max day from DB instead of relying on 'days' variable
                max_day_task = tasks_collection.find_one(
                    {"user_name": user_name},
                    sort=[("day", -1)]
                )
                existing_max_day = max_day_task["day"] if max_day_task else 0
                new_day_num = st.number_input("Day Number", min_value=1, max_value=365,
                                              value=existing_max_day + 1, step=1,
                                              key="new_day_num")
            with nd_col4:
                new_day_duration = st.number_input("Duration (hrs)", min_value=0.5,
                                                   max_value=12.0, value=1.0, step=0.5,
                                                   key="new_day_dur")

            add_new_day_clicked = st.form_submit_button("➕ Add Task", type="primary",
                                                         use_container_width=True)

            if add_new_day_clicked:
                if not new_day_subject.strip():
                    st.error("Please enter a subject name.")
                else:
                    new_task_doc = {
                        "user_name": user_name,
                        "day": int(new_day_num),
                        "subject": new_day_subject.strip(),
                        "topic": new_day_topic.strip() if new_day_topic.strip() else "General Study",
                        "duration": new_day_duration,
                        "status": "pending",
                        "created_at": datetime.now()
                    }
                    try:
                        tasks_collection.insert_one(new_task_doc)
                        st.success(f"✅ New task added: {new_day_subject.strip()} – Day {int(new_day_num)}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to add task: {e}")

        st.markdown("---")

        # ---- Section 3: Danger Zone – Reset All Data ----
        st.markdown("""
        <div class="danger-zone">
            <div class="danger-zone-title">⚠️ Danger Zone</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        st.caption("These actions are irreversible. All data will be permanently deleted.")

        reset_confirm_key = "confirm_reset_all"
        if reset_confirm_key not in st.session_state:
            st.session_state[reset_confirm_key] = False

        if not st.session_state[reset_confirm_key]:
            if st.button("🗑️ Reset All Study Data", type="secondary", use_container_width=True):
                st.session_state[reset_confirm_key] = True
                st.rerun()
        else:
            st.error("⚠️ **WARNING:** This will permanently delete ALL study plans, tasks, and productivity logs!")

            reset_col1, reset_col2 = st.columns(2)
            with reset_col1:
                if st.button("🗑️ Yes, Delete Everything", key="yes_reset", type="primary",
                              use_container_width=True):
                    try:
                        plans_collection.delete_many({"user_name": user_name})
                        tasks_collection.delete_many({"user_name": user_name})
                        logs_collection.delete_many({"user_name": user_name})
                        collection.delete_many({"name": user_name})

                        # Clear session state
                        if "generated_schedule" in st.session_state:
                            del st.session_state["generated_schedule"]
                        if "plan_user" in st.session_state:
                            del st.session_state["plan_user"]

                        st.session_state[reset_confirm_key] = False
                        st.success("✅ All study data has been reset.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Failed to reset: {e}")

            with reset_col2:
                if st.button("❌ Cancel", key="no_reset", use_container_width=True):
                    st.session_state[reset_confirm_key] = False
                    st.rerun()

        st.markdown("---")

        # ---- Section 4: Delete Individual Productivity Logs ----
        st.markdown("### 📊 Manage Productivity Logs")

        all_logs = list(logs_collection.find({"user_name": user_name}).sort("logged_at", -1).limit(20))

        if not all_logs:
            st.info("No productivity logs found.")
        else:
            st.caption(f"Showing latest {len(all_logs)} log(s). Click delete to remove individual entries.")

            for log in all_logs:
                log_id = str(log["_id"])
                log_date = log.get("date", "N/A")
                log_subj = log.get("subject", "N/A")
                log_topic = log.get("topic", "N/A")
                log_hrs = log.get("hours_studied", 0)

                col1, col2, col3, col4, col5 = st.columns([2, 2.5, 2.5, 1.5, 1.5])

                with col1:
                    st.write(f"📅 {log_date}")
                with col2:
                    st.write(f"📚 {log_subj}")
                with col3:
                    st.write(f"📖 {log_topic}")
                with col4:
                    st.write(f"⏱️ {log_hrs}h")
                with col5:
                    log_confirm_key = f"confirm_del_log_{log_id}"
                    if log_confirm_key not in st.session_state:
                        st.session_state[log_confirm_key] = False

                    if not st.session_state[log_confirm_key]:
                        if st.button("🗑️", key=f"del_log_{log_id}"):
                            st.session_state[log_confirm_key] = True
                            st.rerun()
                    else:
                        if st.button("✅ Confirm", key=f"yes_log_{log_id}"):
                            logs_collection.delete_one({"_id": ObjectId(log_id)})
                            st.session_state[log_confirm_key] = False
                            st.success("✅ Log entry deleted.")
                            st.rerun()