#!/usr/bin/env ruby

# This is meant to parse the third-party-license-info.csv file that
# is output by the npm-license-check script.

require 'csv'

modules = {}

CSV.foreach('third-party-license-info.csv', headers: true) do |row|
  module_full_name = row['module name']
  module_full_name = module_full_name[1..-1] if module_full_name.start_with?('@')
  module_name, module_version = module_full_name.split('@')
  module_version = module_version.to_f

  module_info = modules[module_name] || {
    name: module_name,
    version: module_version,
    license: row['license'],
    repository: row['repository']
  }
  module_info[:version] = [module_info[:version], module_version].max
  modules[module_name] = module_info
end

puts [
  'Name',
  'License',
  'Modified?',
  'URL',
  'License Compliance / Notes'
].to_csv

modules.keys.sort.each do |module_name|
  module_info = modules[module_name]
  puts [
    module_info[:name],
    module_info[:license],
    'NO',
    module_info[:repository],
    nil
  ].to_csv
end
