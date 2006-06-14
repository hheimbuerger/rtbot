module SourceHelper
  def build_branch(branch, indent, output)
    branch.sort {|a,b|
                         if a[1].has_key?(:subentries)==b[1].has_key?(:subentries) then
                             a[0] <=> b[0]
                         else
                             if(a[1].has_key?(:subentries) and not b[1].has_key?(:subentries))
                                 -1
                             else
                                 1
                             end
                         end
                        }.each do |caption, entry|
      if(entry.has_key?(:subentries))
        output << {:type => :dir, :caption => caption, :indent => indent.to_s(), :data => entry}
        #result += "<p class=\"indent" + indent.to_s() + "\"> [DIR] " + caption + "</p>"
        #render :partial => 'manager/file', :locals => {:indent => indent.to_s(),
        #                                       :caption => caption}
        
        build_branch(entry[:subentries], indent+1, output)
      else
        #result += "<p class=\"indent" + indent.to_s() + "\"> [FILE] " + caption + "</p>"
        output << {:type => :file, :caption => caption, :indent => indent.to_s(), :data => entry}
      end
    end
  end

  def self.reloadable?
    false
  end

#    if(branch.has_key?(:dirs))
#      branch[:dirs].each do |name, contents|
#        result += "<p class=\"indent" + indent.to_s() + "\"> [DIR] " + name + "</p>"
#        result += print_branch(contents, indent+1)
#      end
#    end
#    if(branch.has_key?(:files))
#      branch[:files].each do |file|
#        result += "<p class=\"indent" + indent.to_s() + "\"> [FILE] " + file[:filename] + "</p>"
#      end
#    end
end
