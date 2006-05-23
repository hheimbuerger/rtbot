class ManagerController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
    @my_dir = Dir.new(BOT_PATH + "plugins/")
    #filelist = my_dir.entries("*.py")
  end
end
