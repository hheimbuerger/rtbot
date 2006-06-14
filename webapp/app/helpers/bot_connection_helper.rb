module BotConnectionHelper

	def get_status
	    begin
	      bot = ActionWebService::Client::XmlRpc.new(BotApi, BOT_URI)
	      @has_connection = true
	      @state, @num_plugins, @num_events = bot.getStatus
	    rescue Errno::ECONNREFUSED, Errno::EBADF
	      @has_connection = false
 	      @state, @num_plugins, @num_events = nil, nil, nil
	    end
	end

	def get_plugin_status_list
	    begin
	      bot = ActionWebService::Client::XmlRpc.new(BotApi, BOT_URI)
	      @has_connection = true
	      #print "bot: #{bot.inspect}\n"
	      #print "bot.pluginStatusList: #{bot.pluginStatusList.inspect}\n"
	      @plugins = bot.pluginStatusList
	    rescue Errno::ECONNREFUSED, Errno::EBADF
	      @has_connection = false
	      @plugins = nil
	    end
	end

	def enable_plugin(plugin)
	    begin
          bot = ActionWebService::Client::XmlRpc.new(BotApi, BOT_URI)
	      bot.enablePlugin plugin
	    rescue Errno::ECONNREFUSED, Errno::EBADF
	    end
	end

	def disable_plugin(plugin)
	    begin
	      bot = ActionWebService::Client::XmlRpc.new(BotApi, BOT_URI)
	      bot.disablePlugin plugin
	    rescue Errno::ECONNREFUSED, Errno::EBADF
	    end
	end

    def self.reloadable?
        true
    end

end
