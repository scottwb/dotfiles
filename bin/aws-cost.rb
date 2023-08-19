#!/usr/bin/env ruby

require 'json'
require 'csv'

instance_types={
  "r5.2xlarge" => 0.504,
  "m5.xlarge"  => 0.192,
  "t3.xlarge"  => 0.1664,
  "t2.medium"  => 0.0464,
  "c5.xlarge"  => 0.17,
  "m5.2xlarge" => 0.384
}

puts [
  "region",
  "name",
  "type",
  "hourly cost"
].to_csv
['us-east-1', 'us-east-2', 'eu-central-1'].each do |region|
  data = `aws --profile rmarkbio --region #{region} ec2 describe-instances`
  JSON.parse(data)['Reservations'].each do |reservation|
    reservation['Instances'].each do |instance|
      puts [
        region,
        instance['Tags'].find{|t| t['Key'] == 'Name'}['Value'],
        instance['InstanceType'],
        instance_types[instance['InstanceType']]
      ].to_csv
    end
  end
end
