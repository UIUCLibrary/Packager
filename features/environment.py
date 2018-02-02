import tempfile

def before_scenario(context, scenario):

    context._temp_dir = tempfile.TemporaryDirectory()
    context.temp_dir = context._temp_dir.name

def after_scenario(context, scenario):
    context._temp_dir.cleanup()
