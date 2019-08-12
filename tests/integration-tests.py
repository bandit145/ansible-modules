#!/usr/bin/env python

import argparse
import ansible_runner
import os

parser = argparse.ArgumentParser(description='integration test runner')
parser.add_argument('-t', '--tags', help='tags for ansible playbook')
parser.add_argument('-m','--module', help='module to test')
parser.add_argument('--path', help='test path location', default='integrations')
args = parser.parse_args()

def create_runner(extravars):
	rc = ansible_runner.runner_config.RunnerConfig(tags=args.tags, playbook='integrations.yml', project_dir='.', private_data_dir='.', extravars=extravars)
	rc.prepare()
	return ansible_runner.runner.Runner(config=rc)

def main():
	if not args.module:
		for module in os.listdir(args.path):
			runner = create_runner({'module':module})
			runner.run()
	else:
		runner = create_runner({'module':args.module})
		runner.run()
	for line in runner.stdout:
		print(line)


if __name__ == '__main__':
	main()