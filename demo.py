#!/usr/bin/env python

# -*- coding: utf-8 -*-
import json
from textwrap import dedent
import argparse
from agno.agent.agent import Agent
from agno.models.aws.claude import Claude
from anthropic import AnthropicBedrock
from agno.tools.toolkit import Toolkit
import boto3

_instructions = """
You are DemoCreds, a demo agent for credential outcomes for AI services. You are
an expert in calling s3 services on AWS.

## Instructions:
Follow the instructions carefully. You are an agent for interacting with some AWS s3 services on AWS.
You may only use the tools provided to you. You cannot use any other tools or the internet. You
Do not write code, you just call tools.
Run the tools as many times as needed to get the desired result. If an error cannot be overcome, report that
to the user.

## Expected Output:
The result of the given user instructions.
"""

def parse_args():
    parser = argparse.ArgumentParser(description="A simple demo of Agno and credentials of clients.")
    parser.add_argument(
        "--user-profile",
        type=str,
        default="di",
        help="The AWS tool profile to use. Default is 'di'.",
    )
    return parser.parse_args()


class AWSBoto3(Toolkit):
    name: str = "AWSReadOnlyS3"
    description: str = "A tool for interacting with AWS services using Boto3 for read only operations on S3"

    def __init__(self, aws_profile: str = "di", aws_region: str = "us-east-1"):
        super().__init__()
        self.session = boto3.Session(profile_name=aws_profile)
        self.s3 = self.session.client("s3", region_name=aws_region)
        
        for f in [
            self.run_s3_command,
        ]:
            self.register(f)
    
    def run_s3_command(self, command: str, args: dict[str, str] = {}, limit: int = 2500) -> str:
        """Run a command on S3. This tool uses boto3 to run the command.
        The command is the name of the boto3 method to call (for example, list_buckets).
        The args are the arguments to pass to the command. The args should be a dictionary
        with the argument names as keys and the argument values as values. You can leave
        blank if it is not needed. The call to the s3 client is done like this:
        res = getattr(self.s3, command)(**args)
        The result is returned as a string with the repr() of the result.
        NOTE: YOU MAY NOT RUN ANY NON-READ-ONLY COMMANDS. THIS TOOL IS FOR READ ONLY OPERATIONS ONLY.
        Use limits when possible or appropriate. The default is 2500 characters and limits are frugal
        so they are good.

        Args:
            command: The command to run
            args: The arguments for the command
            limit: limit the nubmer of characters in the result to this number. This is useful for
                limiting the size of the result. The default is 2500 characters.

        Returns:
            The result of the command
        """
        res = getattr(self.s3, command)(**args)
        return repr(res)[:limit]

class DemoAgent(Agent):
    def __init__(self, user_profile):
        aws_s3 = AWSBoto3(
            aws_region="us-east-1",
            aws_profile=user_profile,
        )
            
        super().__init__(
            model=Claude(
                id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                client=AnthropicBedrock(
                    aws_region="us-east-1",
                    aws_profile="di",
                )
            ),
            tools=[
                aws_s3
            ],
            instructions=dedent(_instructions),
            description=dedent("You are an agent for interacting with some AWS s3 services on AWS."),
            add_datetime_to_instructions=True,
            show_tool_calls=True,
            debug_mode=True,
            markdown=True,
            parse_response=True,
        )


def main():
    args = parse_args()
    user_profile = args.user_profile

    # Example usage of the user_profile
    print(f"Using AWS tool profile: {user_profile}")
    prompt = input("Enter a prompt to the agnet: ")
    agent = DemoAgent(user_profile=user_profile)
    agent.print_response(prompt)
    print("Done!")

if __name__ == "__main__":
    main()