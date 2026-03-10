require 'asciidoctor'
require 'asciidoctor/extensions'

module SectionRolePropagation
  TARGET_ROLES = %w[added changed removed].freeze

  def self.wrap_inline(text, role)
    body = text.to_s
    return body if body.strip.empty?
    return body if body.include?("[.#{role}]#")
    "[.#{role}]##{body}#"
  end

  def self.rewrite_lines(lines)
    out = []
    roles_by_level = {}
    pending_role = nil

    lines.each do |line|
      trailing_ws = line[/\s*\z/] || ''
      raw = line.sub(/\s*\z/, '')
      stripped = raw.strip

      # if we're in a role context and encounter a discrete block attribute,
      # merge the role into the attribute line so the discrete heading inherits it
      if stripped == '[discrete]'
        active_role = roles_by_level[roles_by_level.keys.max]
        if active_role
          out << "[discrete,#{active_role}]#{trailing_ws}"
          next
        end
      end

      if (m = stripped.match(/^\[\.(added|changed|removed)\]$/))
        pending_role = m[1]
        out << line
        next
      end

      if (m = raw.match(/^(=+)\s+(.+)$/))
        level = m[1].length
        roles_by_level.delete_if { |k, _| k >= level }
        if pending_role
          roles_by_level[level] = pending_role
          pending_role = nil
        end
        active_role = roles_by_level[level]
        if active_role.nil?
          parent_level = roles_by_level.keys.select { |k| k < level }.max
          active_role = parent_level ? roles_by_level[parent_level] : nil
        end
        out << if active_role
                 "#{m[1]} #{wrap_inline(m[2], active_role)}#{trailing_ws}"
               else
                 line
               end
        next
      end

      if pending_role
        active_role = pending_role
        pending_role = nil
      else
        active_role = roles_by_level[roles_by_level.keys.max]
      end
      unless active_role
        out << line
        next
      end

      if stripped.empty? ||
         stripped.start_with?('[', ':', 'include::', 'ifdef::', 'ifndef::', 'endif::',
                              '|===', '.', '//', 'image::', 'link:') ||
         %w[---- .... ==== **** ++++].include?(stripped) ||
         raw.lstrip.start_with?('|')
        out << line
        next
      end

      if (m = raw.match(/^(\s*(?:\*|-|\d+\.)\s+)(.+)$/))
        out << "#{m[1]}#{wrap_inline(m[2], active_role)}#{trailing_ws}"
        next
      end

      if (m = raw.match(/^(\s*(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION):\s+)(.+)$/))
        out << "#{m[1]}#{wrap_inline(m[2], active_role)}#{trailing_ws}"
        next
      end

      out << "#{wrap_inline(raw, active_role)}#{trailing_ws}"
    end

    out
  end
end

Asciidoctor::Extensions.register do
  include_processor do
    process do |doc, reader, target, attrs|
      include_path, = doc.normalize_system_path(target, reader.dir, nil, target_name: 'include file')
      next false unless include_path && ::File.file?(include_path)

      source = ::File.read(include_path, mode: 'r:bom|utf-8')
      rewritten = SectionRolePropagation.rewrite_lines(source.lines)
      reader.push_include(rewritten, include_path, target, 1, attrs)
      true
    end
  end
end
