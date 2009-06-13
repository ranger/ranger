module Color
	@hostname = green, default, bold
	@currentdir = blue, default, bold
	@currentfile = white, default, bold

	@base = default, df

	@link = cyan, default
	@directory = blue, default
	@media = pink, default
	@executable = green, default


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

