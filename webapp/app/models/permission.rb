class Permission < ActiveRecord::Base
  has_and_belongs_to_many :users
  
  def isUserAllowed(id)
#    breakpoint "a"
    users.each do |user|
      if(user.id === id)
        return(true)
      end
    end
    return(false)
  end
end
