class PermissionController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
    @permissions = Permission.find_all
    user = @session[:user]
#    breakpoint "Breaking"
  end

  def access_denied
    flash.now['notice']  = "Permission denied!"
    redirect_to :action => 'index'
  end

end
