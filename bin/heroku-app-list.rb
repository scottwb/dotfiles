#!/usr/bin/env ruby
# coding: utf-8

require 'csv'

def usage
  puts
  puts "Usage: heroku-app-list.rb <heroku-team>"
  puts
  exit -1
end

VALID_CUSTOMERS = [
  'abbvie',
  'acme',
  'avenga',
  'forma',
  'rmarkbio',
  'takeda',
  'ubuild',
  'xeris',
]

VALID_ENVS = [
  'qa',
  'beta',
  'prod',
  'prod2',
  'prod3',
  'stag',
  'stage',
  'delta',
  'jgroh',
]

team = ARGV[0]
usage if team.nil?

def get_app_name_components(app_name)
  service  = nil
  customer = nil
  env      = nil

  parts = app_name.split('-')
  parts.each do |part|
    if VALID_CUSTOMERS.include?(part)
      customer = part
    elsif VALID_ENVS.include?(part)
      env = part
    end
  end
  parts.reject! { |part| [customer, env].include?(part) }

  service  = parts.join('-')

  [service, customer, env]
end

def get_dyno_count(app_name)
  states = [
    :initial,
    :read_types_section,
    :read_types_header,
    :read_totals_section,
    :read_totals_header
  ]
  state = :initial

  dyno_types = {
    'Standard-1X' => 0,
    'Standard-2X' => 0,
    'Private-S'   => 0,
    'Private-M'   => 0,
    'Private-L'   => 0,
  }

  `heroku ps:type -a #{app_name}`.each_line do |line|
    next if line =~ /^\s*$/

    case state
    when :initial
      if line.start_with? '==='
        state = :read_types_section
      end

    when :read_types_section
      if line.start_with? '───'
        state = :read_types_header
      end

    when :read_types_header
      if line.start_with? '==='
        state = :read_totals_section
      end

    when :read_totals_section
      if line.start_with? '───'
        state = :read_totals_header
      end

    when :read_totals_header
      dyno_type, dyno_count = line.split(/\s+/)
      dyno_count = dyno_count.to_i
      dyno_types[dyno_type] ||= 0
      dyno_types[dyno_type] += dyno_count

    end

  end

  return dyno_types
end

csv_header = [
  'Service',
  'Customer',
  'Environment',
  'Heroku App',
  'Heroku Region',
  'Dynos: Standard-1X',
  'Dynos: Standard-2X',
  'Dynos: Private-S',
  'Dynos: Private-M',
  'Dynos: Private-L',
]
puts csv_header.to_csv

apps = `heroku apps -t #{team}`
apps.each_line do |line|
  next if line.start_with? '==='
  next if line =~ /^\s*$/

  app_name, region = line.split(/\s+/)
  app_region = case region&.gsub(/[()]/, '')&.downcase
           when 'eu'        then 'Common EU'
           when 'virginia'  then 'rmb-usa'
           when 'frankfurt' then 'rmb-germany'
           else                  'Common US'
           end

  app_service, app_customer, app_env = get_app_name_components(app_name)
  dyno_types = get_dyno_count(app_name)

  csv_row = [
    app_service,
    app_customer,
    app_env,
    app_name,
    app_region,
    dyno_types['Standard-1X'],
    dyno_types['Standard-2X'],
    dyno_types['Private-S'],
    dyno_types['Private-M'],
    dyno_types['Private-L'],
  ]
  puts csv_row.to_csv

end
