# Compatible with ranger 1.6.0 through 1.7.*
#
# This is a sample plugin that displays "Hello World" in ranger's console after
# it started.

# We are going to extend the hook "ranger.api.hook_ready", so first we need
# to import ranger.api:
import ranger.api

# Save the previously existing hook, because maybe another module already
# extended that hook and we don't want to lose it:
old_hook_ready = ranger.api.hook_ready

# Create a replacement for the hook that...


def hook_ready(fm):
    # ...does the desired action...
    fm.notify("Hello World")
    # ...and calls the saved hook.  If you don't care about the return value,
    # simply return the return value of the previous hook to be safe.
    return old_hook_ready(fm)

# Finally, "monkey patch" the existing hook_ready function with our replacement:
ranger.api.hook_ready = hook_ready
