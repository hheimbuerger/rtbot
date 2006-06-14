module BotConnectionHelper

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

    def get_logging_ticket
      begin
        bot = ActionWebService::Client::XmlRpc.new(BotApi, "http://localhost:8000/")
        ticket = bot.RetrieveLogWatchTicket
        
        render :text => "Register: Registered and got the ID #{ticket}.<br/>"
      rescue Errno::ECONNREFUSED, Errno::EBADF
        render :text => "Register: Can't connect to the bot via XML-RPC.<br/>"
      end
    end



    def self.reloadable?
        true
    end

end
