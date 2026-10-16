"""Local application theme; no external fonts, scripts, or tracking."""

THEME = """
<style>
:root { --ink:#172036; --muted:#778198; --line:#e5e9f1; --blue:#4255f5; }
html,body,[class*="css"],.stApp {font-family:'Segoe UI',Inter,-apple-system,sans-serif;}
.stApp {background:#f6f8fc;color:var(--ink);}
[data-testid="stAppHeader"] {background:transparent;height:2.5rem;}
[data-testid="stToolbarActions"],#MainMenu,footer {display:none;}
[data-testid="stSidebarCollapsedControl"] {display:flex!important;visibility:visible!important;color:#172036;z-index:100000;}
[data-testid="stMainBlockContainer"] {max-width:1580px;padding:2.3rem 3rem 3rem;}
[data-testid="stSidebar"] {background:#10182b;border-right:1px solid #1e293e;min-width:244px;max-width:244px;}
[data-testid="stSidebar"]>div:first-child {padding-top:1.6rem;}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {color:#a7b1c6;}
[data-testid="stSidebar"] button {background:transparent;border:0;color:#aeb9cf;justify-content:flex-start;box-shadow:none!important;padding:.7rem 1rem;border-radius:8px;min-height:43px;font-weight:500;}
[data-testid="stSidebar"] button:hover {background:#1a2540;color:white;}
[data-testid="stSidebar"] button[kind="primary"] {background:#3049df;color:white;}
[data-testid="stSidebar"] button[kind="primary"] [data-testid="stMarkdownContainer"] {color:white;}
[data-testid="stSidebar"] .stLinkButton a {background:transparent;border-color:#2a3650;color:#aeb9cf;justify-content:flex-start;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.35rem;}
.brand {display:flex;align-items:center;gap:11px;color:white;font-size:25px;font-weight:720;letter-spacing:-1px;margin:0 0 28px 6px;}
.brand-mark {width:34px;height:36px;border:1px solid #596aff;border-radius:9px;display:grid;place-items:center;background:#3346c7;color:white;font-size:23px;font-weight:750;}
.brand span:last-child {color:#a7b5ff;font-size:9px;border:1px solid #3d496b;padding:2px 5px;border-radius:4px;letter-spacing:1px;margin-left:1px;}
.workspace-label {font-size:10px;letter-spacing:1.5px;font-weight:650;color:#687993;margin:24px 10px 10px;}
.workspace-switch {background:#182237;border:1px solid #2b354c;border-radius:9px;padding:12px;display:flex;gap:10px;align-items:center;margin-bottom:14px;}
.avatar {width:30px;height:30px;background:#2a3754;display:grid;place-items:center;border-radius:7px;font-size:11px;color:#d3dafa;font-weight:700;}
.workspace-name {font-size:12px;color:#eff2fb;font-weight:600;}.workspace-detail {font-size:10px;color:#8796b1;margin-top:3px;}
.sidebar-foot {border-top:1px solid #2a344a;margin-top:100px;padding:20px 8px 0;font-size:11px;color:#8493ad;line-height:1.8;}
.live-dot {display:inline-block;width:6px;height:6px;border-radius:50%;background:#53c6a0;margin-right:6px;}
.crumb {font-size:11px;font-weight:500;line-height:1.6;letter-spacing:.2px;color:#8b93a5;margin:0 0 23px;}.crumb b {color:#5d687e;font-weight:500;}.crumb span {padding:0 9px;color:#b8bfcb;}
.page-title {font-size:29px;letter-spacing:-.9px;font-weight:700;line-height:1.2;color:#18223a;margin:0 0 8px;}
.page-subtitle {font-size:13px;color:#7a8499;line-height:1.6;margin-bottom:24px;}
.eyebrow {font-size:10px;color:#8b95aa;text-transform:uppercase;letter-spacing:1.3px;font-weight:650;margin-bottom:10px;}
.pill {display:inline-block;font-size:10px;line-height:1.5;padding:4px 9px;border-radius:5px;border:1px solid #dde3ee;background:#f5f7fc;color:#718099;font-weight:550;}
.pill-blue {color:#4a57da;background:#edf0ff;border-color:#e1e5ff;}.pill-green {color:#178361;background:#ecf9f3;border-color:#d5f0e4;}
.page-topline {display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;}
.stat {padding:17px 20px;background:white;border:1px solid var(--line);border-radius:10px;margin-bottom:18px;min-height:108px;}
.stat-label {font-size:11px;font-weight:500;color:#818ba0;}.stat-value {font-size:27px;letter-spacing:-.8px;color:#24304b;font-weight:650;margin:5px 0 3px;}.stat-note {font-size:10px;color:#97a0b1;}
.section-title {font-size:14px;font-weight:650;color:#27324a;letter-spacing:-.1px;}.section-note {font-size:11px;color:#8992a5;margin:4px 0 15px;}
.filebar {display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e8ecf3;padding:0 0 13px;margin-bottom:12px;}
.filebar strong {font-size:12px;color:#3a4760;}.filebar span {font-size:10px;color:#8e98ad;}
.empty-result {text-align:center;padding:68px 18px 65px;min-height:323px;}
.empty-symbol {display:inline-flex;align-items:center;justify-content:center;width:57px;height:57px;background:#f0f2ff;border:1px solid #e2e7ff;border-radius:15px;color:#6676ed;margin-bottom:18px;font:24px Consolas,monospace;}
.empty-title {font-size:16px;font-weight:600;color:#47536e;margin-bottom:8px;}.empty-copy {font-size:12px;line-height:1.8;color:#919aad;max-width:285px;margin:auto;}
.flow {display:flex;justify-content:center;gap:10px;align-items:center;font-size:9px;color:#9da7ba;margin-top:25px;}.flow b {font-weight:500;background:#f7f9fc;padding:5px 9px;border:1px solid #e7ebf2;border-radius:4px;}
.notice {background:#eef2ff;border:1px solid #e0e6ff;border-radius:8px;padding:13px 16px;color:#65739a;font-size:11px;line-height:1.7;margin:8px 0 20px;}
.notice strong {color:#4556b2;font-weight:600;}
.status-line {display:flex;align-items:center;justify-content:space-between;margin-bottom:15px;}
.verification {font-size:12px;color:#7b879f;line-height:1.7;}
.guard {display:flex;align-items:center;gap:12px;padding:12px 0;color:#8490a5;font-size:11px;line-height:1.7;}.guard-icon {color:#7b8baa;font-size:20px;}
.footnote {color:#9aa4b6;font-size:10px;margin-top:20px;line-height:1.8;}
.model-card {padding:21px;background:#fff;border:1px solid #e1e6ef;border-radius:10px;margin-bottom:18px;}
.model-name {font-size:16px;font-weight:650;letter-spacing:-.3px;color:#27344f;margin:12px 0 8px;}.model-copy {font-size:12px;line-height:1.8;color:#8893a6;}
.step-number {font:600 12px Consolas,monospace;color:#6979ef;background:#eef1ff;display:inline-block;border-radius:7px;padding:8px 10px;}
[data-testid="stVerticalBlockBorderWrapper"]>div {background:white;border-color:#e3e8f1!important;border-radius:10px!important;}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {gap:.75rem;}
div[data-testid="stSelectbox"] label p,div[data-testid="stNumberInput"] label p,div[data-testid="stTextInput"] label p {font-size:11px;color:#7c879c;font-weight:500;}
div[data-baseweb="select"]>div {background:#fff;border-color:#dfe5ef;border-radius:7px;min-height:39px;font-size:12px;}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input {background:#fff;font-size:12px;}
[data-testid="stTextArea"] textarea {font:12px/1.8 Consolas,'Cascadia Code',monospace;background:#fbfcff;color:#394963;}
.stButton button,.stDownloadButton button,.stLinkButton a {border-radius:7px;font-size:12px;font-weight:550;min-height:38px;box-shadow:none;}
.stButton button[kind="primary"],.stLinkButton a[kind="primary"] {background:#4255f5;border-color:#4255f5;color:white;}
.stButton button[kind="primary"]:hover {background:#3346e4;border-color:#3346e4;}
.stTabs [data-baseweb="tab-list"] {gap:24px;border-bottom:1px solid #e9edf5;}
.stTabs [data-baseweb="tab"] {font-size:12px;height:39px;color:#8a94a8;padding:0 1px;}
.stTabs [aria-selected="true"] {color:#4255f5!important;font-weight:600;}.stTabs [data-baseweb="tab-highlight"] {background:#4255f5;height:2px;}
[data-testid="stCode"] {border:1px solid #ebeff5;border-radius:8px;background:#f8faff;}
[data-testid="stCode"] pre {font:12px/1.85 Consolas,'Cascadia Code',monospace;max-height:390px;}
h3 {font-size:16px!important;letter-spacing:-.3px!important;} [data-testid="stCaptionContainer"] {font-size:11px;}
[data-testid="stExpander"] {border-color:#e6eaf3!important;border-radius:8px!important;background:#fff;}
[data-testid="stExpander"] summary p {font-size:11px;color:#7b879f;}
[data-testid="stMetricLabel"] p {font-size:11px;} [data-testid="stMetricValue"] {font-size:23px;}
@media(max-width:1000px){[data-testid="stMainBlockContainer"]{padding:2rem 1.25rem;} .page-title{font-size:25px;}.stat{padding:13px;}}
@media(max-width:700px){.empty-result{padding:25px 10px;min-height:200px;}.page-title{font-size:23px;}.stat{min-height:90px;margin-bottom:0;}.st-key-run_metrics [data-testid="stHorizontalBlock"]{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:15px;}.st-key-run_metrics [data-testid="stColumn"]{width:auto!important;min-width:0!important;flex:none!important;}}
</style>
"""
