class LoggedException < ActiveRecord::Base
  set_table_name "exceptions"
  belongs_to :user, :foreign_key => 'handled_by'
  

end
