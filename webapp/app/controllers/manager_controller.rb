class ManagerController < ApplicationController
  before_filter :login_required
  layout 'main'



private
  def do_svn
    base_path = "F:\\Projekte\\Allegiance\\RTBot\\SVN-Sandbox\\bot\\"
    output = `svn status --show-updates --verbose #{base_path}`
    logger.info("Output: " + output)
    re = /^([^?])\s{6}(\*?)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)$/
    results = []
    output.split("\n").each do |line|
      md = re.match(line)
      if(md) then
        #puts(line)
        #puts("|" + md[1] + "|" + md[2] + "|" + md[3] + "|" + md[4] + "|" + md[5] + "|" + md[6] + "|")
        #result_line = (md[1], md[2], md[3], md[4], md[5], md[6])
        resultset = {:state => md[1], :working_rev => md[3], :last_change_rev => md[4], :last_change_author => md[5], :filename => md[6][base_path.length..-1]}
        resultset[:outdated] = (md[2] == '*')
        results << resultset
      #else
        #puts("no match: " + line)
      end
    #  state, outdated, working_rev, last_change_rev, last_change_author, filename = line.scan(
    #  outdated = line[8] ?
    
    #  if(line[0] != '?'[0]) then
    #    puts("|#{line}|")
    #  end
    end
    return(results)
  end

public
  
  def index
    @results = do_svn()
  end
end
