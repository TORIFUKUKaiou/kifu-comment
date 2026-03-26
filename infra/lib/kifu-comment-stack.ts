import * as path from "path";
import * as cdk from "aws-cdk-lib";
import * as apigateway from "aws-cdk-lib/aws-apigateway";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as logs from "aws-cdk-lib/aws-logs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as s3deploy from "aws-cdk-lib/aws-s3-deployment";
import * as cloudfront from "aws-cdk-lib/aws-cloudfront";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import { Construct } from "constructs";

export class KifuCommentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const openaiApiKey = new cdk.CfnParameter(this, "OpenAIApiKey", {
      type: "String",
      noEcho: true,
      description: "OpenAI API Key",
    });

    // Lambda
    const logGroup = new logs.LogGroup(this, "AnalyzerLogGroup", {
      retention: logs.RetentionDays.ONE_DAY,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const analyzerFn = new lambda.Function(this, "AnalyzerFunction", {
      runtime: lambda.Runtime.PYTHON_3_14,
      handler: "handler.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "../../lambda")),
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      logGroup,
      environment: {
        OPENAI_API_KEY: openaiApiKey.valueAsString,
        MODEL: "gpt-5.4-nano",
      },
    });

    // API Gateway
    const api = new apigateway.RestApi(this, "KifuApi", {
      restApiName: "kifu-comment-api",
      deployOptions: { stageName: "prod" },
    });

    const analyze = api.root.addResource("analyze");
    analyze.addMethod("POST", new apigateway.LambdaIntegration(analyzerFn));

    // Frontend hosting
    const siteBucket = new s3.Bucket(this, "SiteBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      autoDeleteObjects: true,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const distribution = new cloudfront.Distribution(this, "SiteDistribution", {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      additionalBehaviors: {
        "/api/*": {
          origin: new origins.RestApiOrigin(api),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
      },
      defaultRootObject: "index.html",
    });

    new s3deploy.BucketDeployment(this, "DeploySite", {
      sources: [s3deploy.Source.asset(path.join(__dirname, "../../frontend"))],
      destinationBucket: siteBucket,
      distribution,
      distributionPaths: ["/*"],
    });

    // Outputs
    new cdk.CfnOutput(this, "ApiEndpoint", {
      value: `${api.url}analyze`,
    });
    new cdk.CfnOutput(this, "SiteUrl", {
      value: `https://${distribution.distributionDomainName}`,
    });
  }
}
