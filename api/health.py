def handler(request):
    # Simple health check for Vercel serverless function
    return {
        "statusCode": 200,
        "headers": {"content-type": "application/json"},
        "body": '{"ok": true, "message": "health check"}'
    }
