class SourceController < ApplicationController
  #before_filter :login_required
  layout 'main'
  include SvnProxy
  include FileHelper
  include ApplicationHelper

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: requires 'viewsrc'
  # update: logged in, detailed check is performed in the action
  allow_with_permission :action => 'index', :required_permission => 'viewsrc'
  allow_with_permission :action => 'update', :required_permission => nil

public
  
  def index
    @raw_results = retrieve_status()
  end
  
  def update
    path = @params[:path]
    if(path =~ /^plugins[\/\\][a-zA-Z]Plugin.py$/)
        if(has_permission?('updcore') or has_permission?('updplugins'))
            @command_line_result = force_update(@params[:path])
        else
            access_denied!(this, 'updplugins')
        end
    else
        if(has_permission?('updcore'))
            @command_line_result = force_update(@params[:path])
        else
            access_denied!(this, 'updcore')
        end
    end
    #redirect_to :action => index, :params => {:command_line_result => command_line_result}
    #render :action => index, :params => {:command_line_result => command_line_result}
    #render :text => result
  end
end
