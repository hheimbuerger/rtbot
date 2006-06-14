class LoggedExceptionController < ApplicationController
  #before_filter :login_required
  include ApplicationHelper
  layout 'main'

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # index: requires 'viewexc'
  # view: requires 'viewexc'
  # confirm: requires 'confexc'
  # reopen: requires 'confexc'
  # delete: requires 'delexc'
  allow_with_permission :action => 'index', :required_permission => 'viewexc'
  allow_with_permission :action => 'view', :required_permission => 'viewexc'
  allow_with_permission :action => 'confirm', :required_permission => 'confexc'
  allow_with_permission :action => 'reopen', :required_permission => 'confexc'
  allow_with_permission :action => 'delete', :required_permission => 'delexc'

  def index
    @logged_exceptions = LoggedException.find_all
  end

  def view
    @logged_exception = LoggedException.find(params[:id])
  end
  
  def confirm
    if(request.post?)
      @logged_exception = LoggedException.find(params[:id])
      @logged_exception.user = @session[:user]
      @logged_exception.handled_when = Time.new
      if @logged_exception.save
        flash[:note] = "Exception confirmed."
        redirect_to :controller => 'logged_exception', :action => 'index'
      else
        flash[:note] = "Error."
        redirect_to :action => 'view', :id => params[:id]
      end
    else
      # DEBUG: should give error for non-POST
      redirect_to :controller => 'status'
    end
  end
  
  def reopen
    if(request.post?)
      @logged_exception = LoggedException.find(params[:id])
      @logged_exception.user = nil
      @logged_exception.handled_when = nil
      if @logged_exception.save
        flash[:note] = "Exception reopened."
        redirect_to :controller => 'logged_exception', :action => 'index'
      else
        flash[:note] = "Error."
        redirect_to :action => 'view', :id => params[:id]
      end
    else
      # DEBUG: should give error for non-POST
      redirect_to :controller => 'status'
    end
  end

  def delete
    if(request.post?)
      LoggedException.delete(params[:id])
      flash[:note] = "Exception deleted."
      redirect_to :action => 'index'
    else
      # DEBUG: should give error for non-POST
      redirect_to :controller => 'status'
    end
  end
end
