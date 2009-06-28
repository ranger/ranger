module Color
	@hostname = green, default, bold
	@currentdir = blue, default, bold
	@currentfile = white, default, bold

	@base = default, df, none

	@link = cyan, default, none
	@directory = blue, default, none
	@media = pink, default, none
	@video = pink, default, none
	@image = yellow, default, none
	@sound = green, default, none
	@executable = green, default, none

	@butt = default, default, none
	@allowed = cyan, default, none
	@denied = pink, default, none
	@date = default, default, bold

	@bar_done = black, cyan, none
	@bar_undone = default, default, none

	module Selected
		@base = blue, default, reverse
		@link = cyan, default, reverse
	end

	module SelectedCurrentRow
		@base = default, df, reverse | bold

		@link = cyan, default, reverse | bold
		@directory = blue, default, reverse | bold
		@media = pink, default, reverse | bold
		@executable = green, default, reverse | bold

		@video = pink, default, reverse | bold
		@image = yellow, default, reverse | bold
		@sound = green, default, reverse | bold
	end
end

