module Color
	@base = df, df

	@link = cyan, df
	@directory = blue, df
	@media = pink, df
	@executable = green, df

	module Selected
		@base = df, df, reverse

		@link = cyan, df, reverse
		@directory = blue, df, reverse
		@media = pink, df, reverse
		@executable = green, df, reverse
	end
end

