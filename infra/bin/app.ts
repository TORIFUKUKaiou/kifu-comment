#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { KifuCommentStack } from "../lib/kifu-comment-stack";

const app = new cdk.App();
new KifuCommentStack(app, "KifuCommentStack");
