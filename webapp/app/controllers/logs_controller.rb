class LogsController < ApplicationController
  before_filter :login_required
  layout 'main'
  include FileHelper

  def index
    @my_dir = Dir.new(BOT_PATH + "logs/")
  end
end
