require 'asciidoctor'
require 'asciidoctor/extensions'

module SectionRolePropagation
  TARGET_ROLES = %w[added changed removed red orange green].freeze

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

      if stripped == '[discrete]'
        active_role = roles_by_level[roles_by_level.keys.max]
        if active_role
          out << "[discrete,#{active_role}]#{trailing_ws}"
          next
        end
      end

      if (m = stripped.match(%r{\A\[\.(added|changed|removed|red|orange|green)\]\z}))
        pending_role = m[1]
        out << line
        next
      end

      if (m = raw.match(/^(=+)\s+(.+)$/))
        level = m[1].length
        roles_by_level.delete_if { |k, _| k >= level }

        inline_role = nil
        if (ir = m[2].match(%r{\A\[\.(added|changed|removed|red|orange|green)\]#(.+)#\z}))
          inline_role = ir[1]
        end

        active_role = pending_role || inline_role
        pending_role = nil if active_role

        if active_role.nil?
          parent_level = roles_by_level.keys.select { |k| k < level }.max
          active_role = parent_level ? roles_by_level[parent_level] : nil
        end

        roles_by_level[level] = active_role if active_role

        if active_role
          out << "#{m[1]} #{wrap_inline(m[2], active_role)}#{trailing_ws}"
        else
          out << line
        end
        next
      end

      active_role = if pending_role
                      pending_role.tap { pending_role = nil }
                    else
                      roles_by_level[roles_by_level.keys.max]
                    end

      unless active_role
        out << line
        next
      end

      skip_line = stripped.empty? ||
                  stripped.start_with?('[', ':', 'include::', 'ifdef::', 'ifndef::', 'endif::', '|===', '.', '//', 'image::', 'link:') ||
                  %w[---- .... ==== **** ++++].include?(stripped) ||
                  raw.lstrip.start_with?('|')
      if skip_line
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
