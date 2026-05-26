import sys
import traceback
sys.path.insert(0, '.')
try:
    from app.api.v1.ai_routes import router
    print('OK')
except Exception as e:
    traceback.print_exc()