import os
import tempfile
from pathlib import Path

# 必须在导入 app 之前设置，让配置指向独立的测试数据目录
_tmp_root = Path(tempfile.mkdtemp(prefix="personal_website_test_"))
os.environ["DATA_DIR"] = str(_tmp_root / "data")
os.environ["TIMEZONE"] = "Asia/Shanghai"
os.environ["AUTH_ENABLED"] = "false"
