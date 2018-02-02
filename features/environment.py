import tempfile
temp_dir = None

def before_scenario(context, scenario):
    global temp_dir
    temp_dir = tempfile.TemporaryDirectory()
    context.temp_dir = temp_dir.name

def after_scenario(context, scenario):
    global temp_dir
    temp_dir.cleanup()
