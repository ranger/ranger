module Application
	## to be extended by data/apps.rb
	extend self
	def self.method_missing(*_) end
	def check(rc)
		assert rc, RunContext
	end
end

