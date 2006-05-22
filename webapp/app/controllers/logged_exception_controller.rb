class LoggedExceptionController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
    if(has_permission?("viewexc"))
      @logged_exceptions = LoggedException.find_all
    else
      redirect_to :controller => 'status'
    end
  end

  def view
    if(has_permission?("viewexc"))
      @logged_exception = LoggedException.find(params[:id])
    else
      redirect_to :controller => 'status'
    end
  end
  
  def confirm
    if(has_permission?("confexc") and request.post?)
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
      redirect_to :controller => 'status'
    end
  end
  
  def reopen
    if(has_permission?("confexc") and request.post?)
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
      redirect_to :controller => 'status'
    end
  end

  def delete
    if(has_permission?("delexc") and request.post?)
      LoggedException.delete(params[:id])
      flash[:note] = "Exception deleted."
      redirect_to :action => 'index'
    else
      redirect_to :controller => 'status'
    end
  end
end
