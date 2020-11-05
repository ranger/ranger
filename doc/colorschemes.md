Colorschemes
============

This text explains colorschemes and how they work.

Context Tags
------------

Context tags provide information about the context and are Boolean values (`True`
or `False`). For example, if the tag `in_titlebar` is set, you probably want to
know about the color of a part of the titlebar now.

The default context tags are specified in `/ranger/gui/context.py` in the
constant `CONTEXT_KEYS`. Custom tags can be specified in a custom plugin file in
`~/.config/ranger/plugins/`. The code to use follows.

```python
# Import the class
import ranger.gui.context

# Add your key names
ranger.gui.context.CONTEXT_KEYS.append('my_key')

# Set it to False (the default value)
ranger.gui.context.Context.my_key = False

# Or use an array for multiple names
my_keys = ['key_one', 'key_two']
ranger.gui.context.CONTEXT_KEYS.append(my_keys)

# Set them to False
for key in my_keys:
    code = 'ranger.gui.context.Context.' + key + ' = False'
    exec(code)
```

As you may or may not have guessed, this only tells ranger that they exist, not
what they mean. To do this, you'll have to dig around in the source code. As an
example, let's walk through adding a key that highlights `README.md` files
differently. All the following code will be written in a standalone plugin file.

First, from above, we'll add the key `readme` and set it to `False`.

```python
import ranger.gui.context

ranger.gui.context.CONTEXT_KEYS.append('readme')
ranger.gui.context.Context.readme = False
```

Then we'll use the hook `hook_before_drawing` to tell ranger that our key is
talking about `README.md` files.

```python
import ranger.gui.widgets.browsercolumn

OLD_HOOK_BEFORE_DRAWING = ranger.gui.widgets.browsercolumn.hook_before_drawing

def new_hook_before_drawing(fsobject, color_list):
    if fsobject.basename === 'README.md':
        color_list.append('readme')

    return OLD_HOOK_BEFORE_DRAWING(fsobject, color_list)

ranger.gui.widgets.browsercolumn.hook_before_drawing = new_hook_before_drawing
```

Notice we call the old `hook_before_drawing`. This makes sure that we don't
overwrite another plugin's code, we just append our own to it.

To highlight it a different color, just [add it to your colorscheme][1]

[1]:#adapt-a-colorscheme

Implementation in the GUI Classes
---------------------------------

The class `CursesShortcuts` in the file `/ranger/gui/curses_shortcuts.py` defines
the methods `color(*tags)`, `color_at(y, x, wid, *tags)` and `color_reset()`.
This class is a superclass of `Displayable`, so these methods are available almost
everywhere.

Something like `color("in_titlebar", "directory")` will be called to get the
color of directories in the titlebar. This creates a `ranger.gui.context.Context`
object, sets its attributes `in_titlebar` and `directory` to True, leaves the
others as `False`, and passes it to the colorscheme's `use(context)` method.

The Color Scheme
----------------

A colorscheme should be a subclass of `ranger.gui.ColorScheme` and define the
method `use(context)`. By looking at the context, this use-method has to
determine a 3-tuple of integers: `(foreground, background, attribute)` and return
it.

`foreground` and `background` are integers representing colors, `attribute` is
another integer with each bit representing one attribute. These integers are
interpreted by the terminal emulator in use.

Abbreviations for colors and attributes are defined in `ranger.gui.color`. Two
attributes can be combined via bitwise OR: `bold | reverse`

Once the color for a set of tags is determined, it will be cached by default. If
you want more dynamic colorschemes (such as a different color for very large
files), you will need to dig into the source code, perhaps add a custom tag and
modify the draw-method of the widget to use that tag.

Run `tc_colorscheme` to check if your colorschemes are valid.

Specify a Colorscheme
---------------------

Colorschemes are searched for in these directories:

- `~/.config/ranger/colorschemes/`
- `/path/to/ranger/colorschemes/`

To specify which colorscheme to use, change the option `colorscheme` in your
rc.conf: `set colorscheme default`.

This means, use the colorscheme contained in either
`~/.config/ranger/colorschemes/default.py` or
`/path/to/ranger/colorschemes/default.py`.

Adapt a colorscheme
-------------------

You may want to adapt a colorscheme to your needs without having a complete copy
of it, but rather the changes only. Say, you want the exact same colors as in
the default colorscheme, but the directories to be green rather than blue,
because you find the blue hard to read.

This is done in the jungle colorscheme `ranger/colorschemes/jungle`, check it
out for implementation details. In short, I made a subclass of the default
scheme, set the initial colors to the result of the default `use()` method and
modified the colors how I wanted.

This has the obvious advantage that you need to write less, which results in
less maintenance work and a greater chance that your colorscheme will work with
future versions of ranger.
