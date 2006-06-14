class AccountController < ApplicationController

  # /=============================================
  # | PERMISSIONS
  # \=============================================
  # login: open
  # switch: open
  # logoutform: logged in, any permission set
  # logout: logged in, any permission set
  allow_with_permission :action => 'logoutform', :required_permission => nil
  allow_with_permission :action => 'logout', :required_permission => nil

  def login
    case @request.method
      when :post
      if @session[:user] = User.authenticate(@params[:user_login], @params[:user_password])

        flash['notice']  = "Login successful"
        redirect_back_or_default :controller => 'status'
        #redirect_back_or_default :action => "welcome"
      else
        flash.now['notice']  = "Login unsuccessful"

        @login = @params[:user_login]
      end
    end
  end
  
  def switch
    if @session[:user].nil?
      render :action => "login"
    else
      render :action => "logoutform"
    end
  end
  
  def logoutform
    
  end
  
  def logout
    @session[:user] = nil
    redirect_to :controller => 'status', :action => 'index'
  end

#  def welcome
#  end
  
end
