class PermissionController < ApplicationController
  #before_filter :login_required
  layout 'main'

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: logged in
  # access_denied: none
  allow_with_permission :action => 'index', :required_permission => nil

private
  def prepare_table_data
    @permissions = Permission.find(:all, :order => "display_order ASC")
  end

public
  def index
    prepare_table_data
  end

  def access_denied
    if(not flash[:errormessage] or not flash[:required_permission] or not flash[:referrer])
      redirect_to :action => 'index'
    end
    #flash.now['notice']  = "Permission denied!"
    #redirect_to :action => 'index'
    @errormessage = flash[:errormessage]
    @required_permission = flash[:required_permission]
    @referrer = flash[:referrer]
    prepare_table_data
  end
  
  def not_logged_in
    
  end

end
