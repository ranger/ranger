def move_between(current, minimum, maximum, relative=0, absolute=None):
	i = current
	if isinstance(absolute, int):
		i = absolute
	if isinstance(relative, int):
		i += relative
	i = max(minimum, min(maximum - 1, i))
	return i
