module Color
	@hostname = green, default, bold
	@currentdir = blue, default, bold
	@currentfile = white, default, bold

	@base = default, df, none

	@link = cyan, default, none
	@directory = blue, default, none
	@media = pink, default, none
	@executable = green, default, none

	@butt = default, default, none
	@allowed = cyan, default, none
	@denied = pink, default, none
	@date = default, default, bold

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
	end
end

