ALLOWED_SETTINGS = """
show_hidden scroll_offset
directories_first sort reverse
preview_files max_history_size colorscheme
collapse_preview auto_load_preview
max_dirsize_for_autopreview autosave_bookmarks
apps keys
""".split()

# -- globalize the settings --

from ranger.ext.openstruct import OpenStruct
class SettingsAware(object):
	settings = OpenStruct()

	@staticmethod
	def _setup():
		from inspect import isclass, ismodule
		from ranger.gui.colorscheme import ColorScheme

		# overwrite single default options with custom options
		from ranger.defaults import options
		try:
			import options as custom_options
			for setting in ALLOWED_SETTINGS:
				if hasattr(custom_options, setting):
					setattr(options, setting, getattr(custom_options, setting))
				elif not hasattr(options, setting):
					raise Exception("Following option was not defined: " + setting)
		except ImportError:
			pass

		# If a module is specified as the colorscheme, replace it with one
		# valid colorscheme inside that module.

		if isclass(options.colorscheme) and \
				issubclass(options.colorscheme, ColorScheme):
			options.colorscheme = options.colorscheme()

		elif ismodule(options.colorscheme):
			for var_name in dir(options.colorscheme):
				var = getattr(options.colorscheme, var_name)
				if var != ColorScheme and isclass(var) \
						and issubclass(var, ColorScheme):
					options.colorscheme = var()
					break
			else:
				raise Exception("The module contains no valid colorscheme!")

		else:
			raise Exception("Cannot locate colorscheme!")

		for setting in ALLOWED_SETTINGS:
			SettingsAware.settings[setting] = getattr(options, setting)

