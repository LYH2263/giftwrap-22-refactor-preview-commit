"""让落档类测例跑在进程内的临时 SQLite 上，与真实数据文件隔离。

必须在任何 app.* 模块导入之前设置 DATA_DIR：app.config 在导入时固化 DB_PATH。
"""
import os
import tempfile

_TMP_DATA = tempfile.mkdtemp(prefix="giftwrap-test-")
os.environ.setdefault("DATA_DIR", _TMP_DATA)
