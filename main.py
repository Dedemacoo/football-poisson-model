import os
import sys

# Proje dizinini Python path'e ve çalışma ortamına ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "football_poisson_model")
if os.path.exists(app_dir):
    sys.path.insert(0, app_dir)
    os.chdir(app_dir)

import dashboard

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    dashboard.run_server(port)
