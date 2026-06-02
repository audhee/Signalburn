"""
API routes for Arohan backend
"""

from .test import router as test_router

# Include all API routers here
api_routers = [
    test_router,
]