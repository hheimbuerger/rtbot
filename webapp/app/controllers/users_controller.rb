class UsersController < ApplicationController
  before_filter :login_required
  layout 'main'

  def index
    #list
    #render :action => 'list'
    redirect_to :action => 'list'
  end

  # GETs should be safe (see http://www.w3.org/2001/tag/doc/whenToUseGet.html)
  verify :method => :post, :only => [ :destroy, :create, :update ],
         :redirect_to => { :action => :list }

  def list
    if(has_permission?("superadmin"))
      #@user_pages, @users = paginate :users, :per_page => 10
      @users = User.find_all
    else
      redirect_to :controller => 'permission', :action => 'access_denied'
    end
  end

#  def show
#    @user = User.find(params[:id])
#    @permissions = Permission.find_all
#  end

  def new
    if(has_permission?("superadmin"))
      @user = User.new
    else
      redirect_to :controller => 'permission', :action => 'access_denied'
    end
  end

  def create
    if(has_permission?("superadmin"))
      @user = User.new(@params[:user])
  #    @user = User.new(:login => params[:user][:login], :occupation => "Code Artist")
  
      if @user.save
        #@session[:user] = User.authenticate(@user.login, @params[:user][:password])
        flash[:notice] = 'User was successfully created.'
        redirect_to :action => 'list'
      else
        render :action => 'new'
      end
    else
      redirect_to :controller => 'permission', :action => 'access_denied'
    end
  end

  def edit
    @user = User.find(params[:id])
    @permissions = Permission.find_all
  end

  def update
    @user = User.find(params[:id])
    @permissions = Permission.find_all

    @user.login = params[:login]
    if(params[:password] != "")
      @user.password = params[:password]
    end

    # save permissions in the database
    @permissions.each do |permission|
      @user.permissions.delete(permission)
      if(@params["permission"][permission.id.to_s()] == "true") then
        @user.permissions << permission
      end
    end
    
#    if @user.update_attributes(params[:user])
    if @user.save
      logger.info("UsersController#update: User saved.")
      flash[:notice] = 'User was successfully updated.'
      redirect_to :action => 'list'
    else
      logger.info("UsersController#update: Saving failed.")
      render :action => 'edit'
    end
  end

  def destroy
    User.find(params[:id]).destroy
    redirect_to :action => 'list'
  end
end
