import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = "data"


SEMESTER_META = {
   "ANON_Fall 2023": {
       "academic_year": "2023-2024",
       "name": "Fall 2023",
       "mid_start": "2023-10-30",
       "mid_end":   "2023-11-10",
       "fin_start": "2023-12-17",
       "fin_end":   "2023-12-23",
   },
   "ANON_Spring 2024": {
       "academic_year": "2023-2024",
       "name": "Spring 2024",
       "mid_start": "2024-03-11",
       "mid_end":   "2024-03-22",
       "fin_start": "2024-05-12",
       "fin_end":   "2024-05-18",
   },
   "ANON_Fall 2024": {
       "academic_year": "2024-2025",
       "name": "Fall 2024",
       "mid_start": "2024-10-23",
       "mid_end":   "2024-10-30",
       "fin_start": "2024-12-15",
       "fin_end":   "2024-12-23",
   },
   "ANON_Spring 2025": {
       "academic_year": "2024-2025",
       "name": "Spring 2025",
       "mid_start": "2025-03-06",
       "mid_end":   "2025-03-13",
       "fin_start": "2025-05-10",
       "fin_end":   "2025-05-19",
   },
}

def load_semester(code: str, meta: dict):
   base = os.path.join(DATA_DIR, code)


   paths = {
       "stats": base + " Student Statistics Full.xlsx",
       "abs":   base + " Absences.xlsx",
       "bl":    base + " Blacklist.xlsx",
   }


   for p in paths.values():
       if not os.path.exists(p):
           raise FileNotFoundError(p)


   stats = pd.read_excel(paths["stats"])
   absences = pd.read_excel(paths["abs"])
   blacklist = pd.read_excel(paths["bl"])


   for df in (stats, absences, blacklist):
       df["SemesterCode"] = code
       df["SemesterName"] = meta["name"]
       df["Academic Year"] = meta["academic_year"]


   return stats, absences, blacklist



def plot_horizontal_bar(series, title, xlabel, top_n=20):
   series = series.sort_values(ascending=False).head(top_n)
   series = series[::-1]


   fig, ax = plt.subplots(figsize=(10, 6), dpi=100)


   y = np.arange(len(series))


   ax.barh(y, series.values, color="#2a7bc0")


   ax.set_yticks(y)
   ax.set_yticklabels(series.index, fontsize=10)


   ax.set_xlabel(xlabel, fontsize=11)
   ax.set_title(f"{title}\n(Top {top_n})", fontsize=13, pad=15)


   max_val = series.values.max()
   for i, v in enumerate(series.values):
       ax.text(v + max_val * 0.02, i, str(v), fontsize=9, va='center')


   plt.tight_layout()
   plt.show()




# LOAD ALL SEMESTERS THAT EXIST


all_stats, all_abs, all_bl = [], [], []


for code, meta in SEMESTER_META.items():
   try:
       s, a, b = load_semester(code, meta)
       all_stats.append(s)
       all_abs.append(a)
       all_bl.append(b)
       print(f"Loaded: {code}")
   except FileNotFoundError:
       print(f"WARNING: files for {code} not found, skipping.")


if not all_stats:
   raise RuntimeError("No semester files found in DATA_DIR.")


stats_all = pd.concat(all_stats, ignore_index=True)
abs_all   = pd.concat(all_abs, ignore_index=True)
bl_all    = pd.concat(all_bl, ignore_index=True)


# Clean out missing IDs
stats_all = stats_all[stats_all["ANON_ID"] != "MISSING_ANON_ID"].copy()
abs_all   = abs_all[abs_all["ANON_ID"]   != "MISSING_ANON_ID"].copy()
bl_all    = bl_all[bl_all["ANON_ID"]    != "MISSING_ANON_ID"].copy()




abs_all["Start Date"] = pd.to_datetime(abs_all["Start Date"])




# 1) TOP ABSENCES BY STUDENT GROUP


id_to_group = (
   stats_all[["ANON_ID", "Student Group"]]
   .drop_duplicates()
   .set_index("ANON_ID")["Student Group"]
)


abs_with_group = abs_all.merge(
   id_to_group.rename("Student Group"),
   left_on="ANON_ID",
   right_index=True,
)


absences_by_group = (
   abs_with_group.groupby("Student Group")["ANON_ID"]
   .size()
   .sort_values()
)


plot_horizontal_bar(
   absences_by_group,
   "Number of Absences by Student Group (2 Years Combined)",
   "Number of absences",
)


# 2) TOP BLACKLISTED GROUPS (ALL YEARS)


bl_with_group = bl_all.merge(
   id_to_group.rename("Student Group"),
   left_on="ANON_ID",
   right_index=True,
)


blacklisted_by_group = (
   bl_with_group.groupby("Student Group")["ANON_ID"]
   .nunique()
   .sort_values()
)


plot_horizontal_bar(
   blacklisted_by_group,
   "Number of Blacklisted Students by Student Group (2 Years Combined)",
   "Number of blacklisted students",
)




# 3) PERCENT OF BLACKLISTED STUDENTS BY ACADEMIC YEAR (PIE)


year_stats = {}


for year in stats_all["Academic Year"].dropna().unique():
   stats_year = stats_all[stats_all["Academic Year"] == year]
   bl_year = bl_all[bl_all["Academic Year"] == year]


   students_with_sessions = set(
       stats_year.loc[stats_year["Session Booked"] > 0, "ANON_ID"]
   )
   students_blacklisted = set(bl_year["ANON_ID"]) & students_with_sessions


   total = len(students_with_sessions)
   bl_count = len(students_blacklisted)
   not_bl = total - bl_count


   year_stats[year] = {
       "total_students": total,
       "blacklisted": bl_count,
       "not_blacklisted": not_bl,
   }


fig, axes = plt.subplots(
   1,
   len(year_stats),
   figsize=(10, 4),
   dpi=120,
   constrained_layout=True
)


if len(year_stats) == 1:
   axes = [axes]


for ax, (year, st) in zip(axes, sorted(year_stats.items())):
   vals = [st["blacklisted"], st["not_blacklisted"]]
   labels = ["Blacklisted", "Not blacklisted"]
   ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90)
   ax.set_title(
       f"Blacklisted students\nAcademic year {year}",
       fontsize=12,
       pad=15
   )


plt.show()




# 4A) BUCKETED PROBABILITY: AFTER HOW MANY SESSIONS THEY START TO MISS


student_level = (
   stats_all.groupby("ANON_ID")
   .agg(
       total_sessions=("Session Booked", "sum"),
       total_absent=("Absent", "sum"),
   )
   .reset_index()
)
student_level["has_absence"] = student_level["total_absent"] > 0




def bucket_sessions(n):
   if n <= 3:
       return "1–3"
   elif n <= 6:
       return "4–6"
   elif n <= 10:
       return "7–10"
   elif n <= 20:
       return "11–20"
   else:
       return "21+"




student_level["Bucket"] = student_level["total_sessions"].apply(bucket_sessions)


bucket_stats = (
   student_level.groupby("Bucket")
   .agg(
       students=("ANON_ID", "count"),
       students_with_absence=("has_absence", "sum"),
   )
)
bucket_stats["share_with_absence"] = (
   bucket_stats["students_with_absence"] / bucket_stats["students"]
)


bucket_stats = bucket_stats.sort_values("share_with_absence", ascending=True)


fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(bucket_stats.index, bucket_stats["share_with_absence"])
ax.set_xlabel("Session count bucket (2 years combined)")
ax.set_ylabel("Students with ≥1 absence")
ax.set_title("Absence probability by session bucket")


for i, v in enumerate(bucket_stats["share_with_absence"]):
   ax.text(i, v + 0.02, f"{v:.2f}", ha="center")


plt.tight_layout()
plt.show()




# 4B) SURVIVAL ANALYSIS: TIME IN SESSIONS UNTIL FIRST ABSENCE


stats_surv = stats_all.sort_values(["ANON_ID"]).copy()
stats_surv["session_order"] = stats_surv.groupby("ANON_ID").cumcount() + 1


first_abs = (
   stats_surv[stats_surv["Absent"] > 0]
   .groupby("ANON_ID")["session_order"]
   .min()
)
total_sessions_id = stats_surv.groupby("ANON_ID")["session_order"].max()


surv = pd.DataFrame({"total_sessions": total_sessions_id})
surv["first_absence_session"] = first_abs
surv["event_observed"] = ~surv["first_absence_session"].isna()
surv["event_time"] = np.where(
   surv["event_observed"],
   surv["first_absence_session"],
   surv["total_sessions"],
)


max_t = int(surv["event_time"].max())
times = list(range(1, max_t + 1))
S = []
s_prev = 1.0


for t in times:
   n_at_risk = (surv["event_time"] >= t).sum()
   d_events = ((surv["event_time"] == t) & surv["event_observed"]).sum()
   if n_at_risk > 0:
       s_prev = s_prev * (1 - d_events / n_at_risk)
   S.append(s_prev)


fig, ax = plt.subplots(figsize=(8, 5))
ax.step(times, S, where="post")
ax.set_xlabel("Session number")
ax.set_ylabel("Probability of never having missed yet")
ax.set_title("Survival curve: staying absence-free vs sessions")
ax.set_ylim(0, 1.05)
plt.tight_layout()
plt.show()




# 5) HEATMAP: ABSENCES PER WEEK OF SEMESTER


abs_week = abs_all.copy()
abs_week["Start Date"] = abs_week["Start Date"].dt.normalize()


week_data = []
for sem_name, df_sem in abs_week.groupby("SemesterName"):
   sem_start = df_sem["Start Date"].min().normalize()
   df_sem = df_sem.copy()
   df_sem["WeekOfSemester"] = ((df_sem["Start Date"] - sem_start).dt.days // 7) + 1
   week_data.append(df_sem)


abs_with_weeks = pd.concat(week_data, ignore_index=True)


pivot_weeks = abs_with_weeks.pivot_table(
   index="SemesterName",
   columns="WeekOfSemester",
   values="ANON_ID",
   aggfunc="count",
   fill_value=0,
)


fig, ax = plt.subplots(figsize=(10, 4))
im = ax.imshow(pivot_weeks.values, aspect="auto")


ax.set_xticks(np.arange(pivot_weeks.shape[1]))
ax.set_xticklabels(pivot_weeks.columns)
ax.set_yticks(np.arange(pivot_weeks.shape[0]))
ax.set_yticklabels(pivot_weeks.index)


ax.set_xlabel("Week of semester")
ax.set_ylabel("Semester")
ax.set_title("Number of absences per week of semester")


cbar = plt.colorbar(im, ax=ax)
cbar.set_label("Number of absences")


plt.tight_layout()
plt.show()




# 6) COHORT ANALYSIS: ABSENCE RATE BY GROUP & ACADEMIC YEAR


def extract_department(group_name: str) -> str:
   if not isinstance(group_name, str) or pd.isna(group_name):
       return "Unknown"
   parts = group_name.split("-")
   if len(parts) >= 2 and parts[1].isalpha():
       return parts[0] + "-" + parts[1]
   return parts[0].strip()


stats_dept = stats_all.copy()
stats_dept["Department"] = stats_dept["Student Group"].apply(extract_department)
stats_dept = stats_dept[stats_dept["Department"] != "Unknown"].copy()


dept_year = (
   stats_dept
   .groupby(["Academic Year", "Department", "ANON_ID"])
   .agg(
       total_sessions=("Session Booked", "sum"),
       total_absent=("Absent", "sum")
   )
   .reset_index()
)
dept_year["has_absence"] = dept_year["total_absent"] > 0


cohort_dept = (
   dept_year
   .groupby(["Academic Year", "Department"])
   .agg(
       students=("ANON_ID", "nunique"),
       abs_students=("has_absence", "sum"),
   )
)
cohort_dept["absence_rate"] = cohort_dept["abs_students"] / cohort_dept["students"]


cohort_dept = cohort_dept.reset_index().sort_values("Department")


pivot_dept = cohort_dept.pivot_table(
   index="Department",
   columns="Academic Year",
   values="absence_rate"
)


data = pivot_dept.to_numpy()
mask = np.isnan(data)
masked_data = np.ma.masked_where(mask, data)


cmap = plt.cm.viridis.copy()
cmap.set_bad("lightgrey")


fig, ax = plt.subplots(
   figsize=(10, max(6, len(pivot_dept) * 0.40)),
   dpi=150,
   constrained_layout=True
)


im = ax.imshow(masked_data, cmap=cmap, aspect="auto", vmin=0, vmax=1)


ax.set_title(
   "Absence Rate by Department (Cohort Analysis)",
   pad=25, fontsize=14
)


ax.set_xticks(np.arange(pivot_dept.shape[1]))
ax.set_xticklabels(
   pivot_dept.columns,
   rotation=0,
   ha="center",
   fontsize=12
)
ax.set_yticks(np.arange(pivot_dept.shape[0]))
ax.set_yticklabels(pivot_dept.index, fontsize=9)


ax.set_xlabel("Academic Year", fontsize=12)
ax.set_ylabel("Department", fontsize=12)




cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label("Absence rate", fontsize=12)




for i in range(pivot_dept.shape[0]):
   for j in range(pivot_dept.shape[1]):
       val = pivot_dept.iloc[i, j]
       if np.isnan(val):
           txt, color = "N/A", "black"
       else:
           txt = f"{val:.2f}"
           color = "white" if val > 0.6 else "black"
       ax.text(j, i, txt, ha="center", va="center", fontsize=7, color=color)


plt.show()


# 7) ABSENCES: BEFORE MIDTERM VS BEFORE FINAL (PER ACADEMIC YEAR)


abs_mid_final = abs_all.copy()
abs_mid_final["date"] = abs_mid_final["Start Date"].dt.normalize()


results_sem = {}
results_year = {}


for code, meta in SEMESTER_META.items():
   sem_name = meta["name"]
   year = meta["academic_year"]


   df_sem = abs_mid_final[abs_mid_final["SemesterName"] == sem_name]
   if df_sem.empty:
       continue


   mid_start = pd.to_datetime(meta["mid_start"])
   mid_end   = pd.to_datetime(meta["mid_end"])
   fin_start = pd.to_datetime(meta["fin_start"])
   fin_end   = pd.to_datetime(meta["fin_end"])


   before_mid = df_sem[df_sem["date"] < mid_start].shape[0]
   before_fin = df_sem[(df_sem["date"] > mid_end) &
                       (df_sem["date"] < fin_start)].shape[0]


   results_sem[sem_name] = {"year": year,
                            "before_midterm": before_mid,
                            "before_final": before_fin}


   if year not in results_year:
       results_year[year] = {"before_midterm": 0, "before_final": 0}
   results_year[year]["before_midterm"] += before_mid
   results_year[year]["before_final"] += before_fin


if results_year:
   fig, axes = plt.subplots(1, len(results_year), figsize=(6 * len(results_year), 6))
   if len(results_year) == 1:
       axes = [axes]


   for ax, (year, vals) in zip(axes, sorted(results_year.items())):
       sizes = [vals["before_midterm"], vals["before_final"]]
       labels = ["Before midterm", "Before final"]
       ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
       ax.set_title(f"Absences: before midterm vs before final\nAcademic year {year}")


   plt.tight_layout()
   plt.show()
