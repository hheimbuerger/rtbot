module SvnProxy

private
  def split_head_directory(input)
    #puts("to split: " + input)
    re = Regexp.new('^((.*?)[\\\\\\/])?(.*)$')    # the character group means "\ or /"
    md = re.match(input)
    return({:head => md[2], :tail => md[3]})
  end
  
  def handle_file(resultset, path, target_tree)
    split_result = split_head_directory(path)
    head = split_result[:head]
    tail = split_result[:tail]
    #puts("Head: " + head.to_s())
    #puts("Tail: " + tail.to_s())
    if(head.nil?)     # last entry, now we're actually adding it to the tree
      #puts("Head.nil")
      #if(not target_tree.has_key?(:files))
      #  #puts("Adding :files")
      #  target_tree[:files] = []
      #end
      #resultset[:filename] = tail
      target_tree[tail] ||= {}              #create unless existing
      target_tree[tail].update(resultset)   #adds the entries of resultset to target_tree[tail]
    else              # entry in the middle, start the function recursively on the head-dir
      #puts("!Head.nil")
      #if(not target_tree.has_key?(head))
      #  #puts("Adding :dirs")
      #  target_tree[head] = {}
      #end
      #if(not target_tree[:dirs].has_key?(head))
      #  target_tree[:dirs][head] = {}
      #end
      #puts("Calling sub")
      target_tree[head] ||= {}
      target_tree[head][:subentries] ||= {}
      handle_file(resultset, tail, target_tree[head][:subentries])
    end
  end
  
public

  def retrieve_status
    # Run SVN
    #base_path = "f:\\Projekte\\Allegiance\\RTBot\\SVN-Sandbox\\bot\\"       # BOT_PATH
    output = `svn status --show-updates --verbose #{BOT_PATH}`
    #logger.info("Output: " + output)
    root = {}
    
    # Parse SVN output
    re = /^([^?])\s{6}(\*?)\s*(\S*)\s*(\S*)\s*(\S*)\s*(\S*)$/
    output.split("\n").each do |line|
      md = re.match(line)
      if(not md.nil?) then
        #puts(md[6])
        if(not md[6][BOT_PATH.length..-1].nil?) then      # special case for the bot\\ directory
          #puts(line)
          #puts("|" + md[1] + "|" + md[2] + "|" + md[3] + "|" + md[4] + "|" + md[5] + "|" + md[6] + "|")
          #result_line = (md[1], md[2], md[3], md[4], md[5], md[6])
          resultset = {:state => md[1], :working_rev => md[3], :last_change_rev => md[4], :last_change_author => md[5], :path => md[6][BOT_PATH.length..-1]}
          #puts(resultset[:path])
          resultset[:outdated] = (md[2] == '*')
          #results << resultset
          
          # Parse results into a hash according to the directory structure
          #print resultset[:path]
          handle_file(resultset, resultset[:path], root)
          
        end
      else
        #puts("no match: " + line)
      end
    end
    
    return(root)
  end
  
  def force_update(path)
    output1 = `svn revert #{BOT_PATH}#{path}`
    output2 = `svn update #{BOT_PATH}#{path}`
    return "#{BOT_PATH}#{path}" + "\n" + output1 + "\n" + output2
  end

end

#def print_branch(branch, indent)
#  if(branch.has_key?(:dirs))
#    branch[:dirs].each do |name, contents|
#      puts("-"*indent + " " + name)
#      print_branch(contents, indent+2)
#    end
#  end
#  if(branch.has_key?(:files))
#    branch[:files].each do |file|
#      puts("*"*indent + " " + file[:filename])
#    end
#  end
#end
  def print_branch(branch, indent)
    result = ""
    branch.each do |caption, entry|
      if(entry.has_key?(:subentries))
        result += "<p class=\"indent" + indent.to_s() + "\"> [DIR] " + caption + "</p>"
        result += print_branch(entry[:subentries], indent+1)
      else
        result += "<p class=\"indent" + indent.to_s() + "\"> [FILE] " + caption + "</p>"
      end
    end
    return(result)
  end

include SvnProxy

#test = split_head_directory("file")
#puts test[:head]
#puts test[:tail]

#root = {}
#resultset = {:state => 'M', :outdated => '*', :working_rev => "1", :last_change_rev => "2", :last_change_author => "nobody", :path => "dir1/dir2/file"}
#handle_file(resultset, resultset[:path], root)
#puts root

file_tree = retrieve_status()
print print_branch(file_tree, 0)