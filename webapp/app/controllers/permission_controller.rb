class PermissionController < ApplicationController
  #before_filter :login_required
  layout 'main'

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: logged in
  # update: logged in, detailed check is performed in the action
  allow_with_permission :action => 'index', :required_permission => 'viewsrc'
  allow_with_permission :action => 'update', :required_permission => nil

  def index
    @permissions = Permission.find(:all, :order => "display_order ASC")
    user = @session[:user]
#    breakpoint "Breaking"
  end

  def access_denied
    #flash.now['notice']  = "Permission denied!"
    #redirect_to :action => 'index'
    @errormessage = flash[:errormessage]
    @required_permission = flash[:required_permission]
    @referrer = flash[:referrer]
    @permissions = Permission.find(:all, :order => "display_order ASC")
  end

end
