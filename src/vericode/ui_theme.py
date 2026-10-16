"""Dark workspace theme; system fonts, no external assets or tracking."""

THEME = """
<style>
:root {--ink:#e4e7ef;--muted:#9299ac;--line:#282d3b;--accent:#a5adff;}
html,body,.stApp {font-family:Inter,'Segoe UI',-apple-system,sans-serif;}
.stApp {background:#0b0d12;color:var(--ink);}
[data-testid="stAppHeader"] {background:#0b0d12;height:2.4rem;}
[data-testid="stToolbarActions"],[data-testid="stAppDeployButton"],.stAppDeployButton,#MainMenu,footer {display:none;}
[data-testid="stSidebarCollapsedControl"] {display:flex!important;visibility:visible!important;z-index:100000;}
[data-testid="stMainBlockContainer"] {max-width:1520px;padding:2.3rem 3.2rem 3rem;}
[data-testid="stSidebar"] {background:#10131b;border-right:1px solid #242936;min-width:245px;max-width:245px;}
[data-testid="stSidebar"]>div:first-child {padding-top:1.5rem;}
[data-testid="stSidebar"] button {background:transparent;border:0;color:#929bb1;justify-content:flex-start;box-shadow:none!important;padding:.65rem .8rem;border-radius:7px;min-height:42px;font-weight:500;}
[data-testid="stSidebar"] button:hover {background:#1b2030;color:#e4e7ef;}
[data-testid="stSidebar"] button[kind="primary"] {background:#252b43;color:#c4caff;}
[data-testid="stSidebar"] button[kind="primary"] [data-testid="stMarkdownContainer"] {color:#c4caff;}
[data-testid="stSidebar"] .stLinkButton a {background:transparent;border-color:#2b3141;color:#929bb1;justify-content:flex-start;}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.3rem;}
.brand {display:flex;align-items:center;gap:10px;color:#f4f5f9;font-size:24px;font-weight:700;letter-spacing:-1px;margin:0 0 27px 5px;}
.brand-mark {width:32px;height:34px;border:1px solid #727ddc;border-radius:8px;display:grid;place-items:center;background:#303958;color:#d9ddff;font-size:21px;}
.brand span:last-child {color:#929bc8;font-size:9px;border:1px solid #3a4159;padding:2px 5px;border-radius:4px;letter-spacing:1px;}
.workspace-label {font-size:10px;letter-spacing:1.7px;font-weight:600;color:#646d82;margin:22px 9px 10px;}
.workspace-switch {border:1px solid #2a2f40;border-radius:8px;padding:12px;display:flex;gap:10px;align-items:center;margin-bottom:8px;background:#161a25;}
.avatar {width:29px;height:29px;background:#29314b;display:grid;place-items:center;border-radius:6px;font-size:10px;color:#c2c9ed;}
.workspace-name {font-size:12px;color:#dce1ef;font-weight:600;}.workspace-detail {font-size:10px;color:#777f96;margin-top:3px;}
.sidebar-foot {border-top:1px solid #282e3c;margin-top:38px;padding:18px 7px 0;font-size:11px;color:#7d879f;line-height:1.9;}
.live-dot {display:inline-block;width:6px;height:6px;border-radius:50%;background:#7bdcb3;margin-right:6px;}
.crumb {font-size:11px;letter-spacing:.3px;color:#747e94;margin:0 0 24px;}.crumb b {color:#a9b1c3;font-weight:500;}.crumb span {padding:0 9px;color:#485065;}
.page-title {font-size:27px;letter-spacing:-.8px;font-weight:650;line-height:1.3;color:#e8ebf4;margin:0 0 7px;}
.page-subtitle {font-size:13px;color:#8c96ad;line-height:1.7;margin-bottom:28px;}
.eyebrow {font-size:10px;color:#a0aad4;letter-spacing:2px;font-weight:600;margin-bottom:22px;}
.hero {padding:36px 0 24px;max-width:850px;}
.hero h1 {font-size:48px!important;letter-spacing:-2px;line-height:1.16;font-weight:650;padding:0;margin:0 0 22px;color:#f2f4fa;}
.hero h1 span {color:#9ca7ea;}.hero p {font-size:15px;color:#9aa4b9;line-height:1.8;max-width:590px;}
.hero-tags {display:flex;gap:23px;flex-wrap:wrap;margin:24px 0 4px;}.hero-tags span {font-size:11px;color:#7f8aa4;}
.hero-tags span:before {content:'✓';color:#8bb6aa;margin-right:7px;}
.overview-footer {font-size:9px;letter-spacing:1.6px;color:#737e95;margin-top:38px;border-top:1px solid #222735;padding-top:22px;}
.overview-footer span {float:right;font-size:11px;letter-spacing:0;color:#7f899e;}
.pill {display:inline-block;font-size:10px;padding:4px 9px;border-radius:5px;border:1px solid #343b50;background:#1b2130;color:#a8b1c9;}
.pill-blue {color:#b0baff;background:#242b45;border-color:#36416a;}.pill-green {color:#8ed8bc;background:#172e28;border-color:#2a5042;}
.stat {padding:20px;background:#131721;border:1px solid var(--line);border-radius:9px;margin-bottom:16px;}
.stat-label {font-size:11px;color:#8a96af;}.stat-value {font-size:28px;color:#e5e9f5;font-weight:600;margin:5px 0;}.stat-note {font-size:10px;color:#6e7b95;}
.section-title {font-size:14px;font-weight:600;color:#dce2f0;}.section-note {font-size:12px;color:#929cb2;margin:5px 0 16px;line-height:1.8;}
.filebar {display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #2a3040;padding-bottom:13px;margin-bottom:12px;}
.filebar strong {font-size:12px;color:#c4cde2;}.filebar span {font-size:9px;color:#7e8aa5;}
.empty-result {text-align:center;padding:65px 18px;min-height:310px;}
.empty-symbol {display:inline-grid;place-items:center;width:52px;height:52px;background:#20263b;border:1px solid #353e60;border-radius:12px;color:#a1b0ef;margin-bottom:18px;font:23px Consolas,monospace;}
.empty-title {font-size:15px;font-weight:550;color:#c7cfe1;margin-bottom:9px;}.empty-copy {font-size:12px;line-height:1.8;color:#8591ab;max-width:290px;margin:auto;}
.flow {display:flex;justify-content:center;gap:12px;align-items:center;font-size:10px;color:#7a88a2;margin-top:25px;}.flow b {font-weight:500;background:#1b2131;padding:5px 8px;border:1px solid #30394e;border-radius:4px;}
.notice {background:#161e31;border:1px solid #2c3856;border-radius:8px;padding:13px 16px;color:#98a8cd;font-size:11px;line-height:1.8;margin:8px 0 20px;}.notice strong {color:#c0cbf3;}
.status-line {display:flex;align-items:center;justify-content:space-between;margin-bottom:15px;}
.verification {font-size:12px;color:#8e9bb5;line-height:1.8;}
.guard {display:flex;align-items:center;gap:12px;padding:12px 0;color:#78859f;font-size:11px;line-height:1.8;}.guard-icon {font-size:20px;}
.model-card {padding:23px;background:#141821;border:1px solid var(--line);border-radius:9px;margin-bottom:18px;min-height:185px;}
.model-name {font-size:16px;font-weight:600;letter-spacing:-.3px;color:#e0e6f3;margin:17px 0 9px;}.model-copy {font-size:12px;line-height:1.9;color:#929db5;margin-bottom:17px;}
.step-number {font:500 11px Consolas,monospace;color:#b2bbef;background:#252c43;display:inline-block;border:1px solid #37415d;border-radius:6px;padding:6px 9px;}
[data-testid="stVerticalBlockBorderWrapper"]>div {background:#131720;border-color:#2a3040!important;border-radius:9px!important;}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {gap:.7rem;}
div[data-testid="stSelectbox"] label p,div[data-testid="stNumberInput"] label p,div[data-testid="stTextInput"] label p {font-size:11px;color:#a1abc0;}
div[data-baseweb="select"]>div {background:#171d2a;border-color:#333c51;border-radius:6px;font-size:12px;}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input {font-size:12px;}
[data-testid="stTextArea"] textarea {font:12px/1.8 Consolas,'Cascadia Code',monospace;color:#d0daf1;}
.stButton button,.stDownloadButton button,.stLinkButton a {border-radius:6px;font-size:12px;font-weight:500;min-height:38px;box-shadow:none;}
.stButton button[kind="primary"] {background:#828ee0;border-color:#828ee0;color:#0e1221;}
.stButton button[kind="primary"]:hover {background:#9aa5f1;border-color:#9aa5f1;}
.stTabs [data-baseweb="tab-list"] {gap:23px;border-bottom:1px solid #293246;}
.stTabs [data-baseweb="tab"] {font-size:12px;height:40px;color:#929fba;padding:0 1px;}
.stTabs [aria-selected="true"] {color:#b0bcff!important;}.stTabs [data-baseweb="tab-highlight"] {background:#939ff0;height:2px;}
[data-testid="stCode"] {border:1px solid #2b3449;border-radius:7px;}[data-testid="stCode"] pre {font:12px/1.85 Consolas,monospace;max-height:390px;}
h3 {font-size:16px!important;}[data-testid="stCaptionContainer"] {font-size:11px;color:#8591a9;}
[data-testid="stExpander"] {border-color:#2b3449!important;border-radius:8px!important;background:#131925;}
[data-testid="stExpander"] summary p {font-size:11px;color:#a2afc9;}
[data-testid="stMetricLabel"] p {font-size:11px;}[data-testid="stMetricValue"] {font-size:23px;}
@media(max-width:1100px){[data-testid="stMainBlockContainer"]{padding:2rem 1.4rem;}.hero h1{font-size:40px!important;}}
@media(max-width:700px){.hero{padding:18px 0;}.hero h1{font-size:34px!important;letter-spacing:-1px;}.hero p{font-size:13px;}.page-title{font-size:24px;}.empty-result{padding:25px 10px;min-height:200px;}.overview-footer span{float:none;display:block;margin-top:12px;}.hero-tags{gap:12px;}}
</style>
"""
