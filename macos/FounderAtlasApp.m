#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>

@interface FounderAtlasApp : NSObject <NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate>
@property (strong) NSWindow *window;
@property (strong) WKWebView *webView;
@property (strong) NSTask *server;
@property (strong) NSURL *serverURL;
@property (strong) NSURL *logURL;
@end

@implementation FounderAtlasApp

- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    NSMenu *menu = [NSMenu new];
    NSMenuItem *appItem = [NSMenuItem new];
    NSMenu *appMenu = [NSMenu new];
    [appMenu addItemWithTitle:@"Founder Atlas 종료" action:@selector(terminate:) keyEquivalent:@"q"];
    appItem.submenu = appMenu;
    [menu addItem:appItem];
    NSMenuItem *viewItem = [NSMenuItem new];
    NSMenu *viewMenu = [[NSMenu alloc] initWithTitle:@"보기"];
    [viewMenu addItemWithTitle:@"새로고침" action:@selector(reloadPage:) keyEquivalent:@"r"];
    viewItem.submenu = viewMenu;
    [menu addItem:viewItem];
    NSApp.mainMenu = menu;

    NSRect frame = NSMakeRect(0, 0, 1120, 820);
    self.window = [[NSWindow alloc] initWithContentRect:frame
        styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
        backing:NSBackingStoreBuffered defer:NO];
    self.window.title = @"Founder Atlas";
    self.window.minSize = NSMakeSize(760, 560);
    [self.window center];
    self.webView = [[WKWebView alloc] initWithFrame:frame];
    self.webView.navigationDelegate = self;
    self.webView.UIDelegate = self;
    self.webView.hidden = YES;
    self.window.contentView = self.webView;
    [self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];

    NSError *error = nil;
    NSURL *content = [self prepareContent:&error];
    if (content && [self startServerWithContent:content error:&error]) return;
    [self showFailure:[NSString stringWithFormat:@"앱을 시작하지 못했습니다.\n%@", error.localizedDescription ?: @"알 수 없는 오류"]];
}

- (void)reloadPage:(id)sender { [self.webView reload]; }
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender { return YES; }
- (void)applicationWillTerminate:(NSNotification *)notification {
    if (self.server.isRunning) [self.server terminate];
}

- (NSURL *)prepareContent:(NSError **)error {
    NSFileManager *fm = NSFileManager.defaultManager;
    NSURL *bundled = [NSBundle.mainBundle.resourceURL URLByAppendingPathComponent:@"content" isDirectory:YES];
    NSURL *support = [[fm URLsForDirectory:NSApplicationSupportDirectory inDomains:NSUserDomainMask].firstObject
        URLByAppendingPathComponent:@"Founder Atlas" isDirectory:YES];
    NSURL *content = [support URLByAppendingPathComponent:@"content" isDirectory:YES];
    if (![fm createDirectoryAtURL:content withIntermediateDirectories:YES attributes:nil error:error]) return nil;
    NSDirectoryEnumerator *enumerator = [fm enumeratorAtURL:bundled includingPropertiesForKeys:@[NSURLIsDirectoryKey] options:0 errorHandler:nil];
    if (!enumerator) {
        if (error) *error = [NSError errorWithDomain:@"FounderAtlas" code:1 userInfo:@{NSLocalizedDescriptionKey: @"콘텐츠를 찾을 수 없습니다."}];
        return nil;
    }
    for (NSURL *source in enumerator) {
        NSString *relative = [source.path substringFromIndex:bundled.path.length + 1];
        NSURL *target = [content URLByAppendingPathComponent:relative];
        NSNumber *isDirectory = nil;
        [source getResourceValue:&isDirectory forKey:NSURLIsDirectoryKey error:nil];
        if (isDirectory.boolValue) {
            if (![fm createDirectoryAtURL:target withIntermediateDirectories:YES attributes:nil error:error]) return nil;
        } else {
            if (![fm createDirectoryAtURL:target.URLByDeletingLastPathComponent withIntermediateDirectories:YES attributes:nil error:error]) return nil;
            if ([fm fileExistsAtPath:target.path] && ![fm removeItemAtURL:target error:error]) return nil;
            if (![fm copyItemAtURL:source toURL:target error:error]) return nil;
        }
    }
    self.logURL = [support URLByAppendingPathComponent:@"server.log"];
    return content;
}

- (BOOL)startServerWithContent:(NSURL *)content error:(NSError **)error {
    NSFileManager *fm = NSFileManager.defaultManager;
    NSURL *resources = NSBundle.mainBundle.resourceURL;
    NSURL *node = [resources URLByAppendingPathComponent:@"node"];
    NSURL *web = [resources URLByAppendingPathComponent:@"web" isDirectory:YES];
    NSURL *serverScript = [web URLByAppendingPathComponent:@"server.js"];
    if (![fm isExecutableFileAtPath:node.path] || ![fm fileExistsAtPath:serverScript.path]) {
        if (error) *error = [NSError errorWithDomain:@"FounderAtlas" code:2 userInfo:@{NSLocalizedDescriptionKey: @"서버 실행 파일이 없습니다."}];
        return NO;
    }
    NSUInteger port = 43000 + arc4random_uniform(10001);
    self.serverURL = [NSURL URLWithString:[NSString stringWithFormat:@"http://127.0.0.1:%lu/", (unsigned long)port]];
    self.server = [NSTask new];
    self.server.executableURL = node;
    self.server.arguments = @[serverScript.path];
    self.server.currentDirectoryURL = web;
    NSMutableDictionary *environment = NSProcessInfo.processInfo.environment.mutableCopy;
    environment[@"PORT"] = [NSString stringWithFormat:@"%lu", (unsigned long)port];
    environment[@"HOSTNAME"] = @"127.0.0.1";
    environment[@"NODE_ENV"] = @"production";
    environment[@"CONTENT_DIR"] = content.path;
    environment[@"PATH"] = [NSString stringWithFormat:@"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:%@", environment[@"PATH"] ?: @""];
    self.server.environment = environment;
    [fm createFileAtPath:self.logURL.path contents:nil attributes:nil];
    NSFileHandle *log = [NSFileHandle fileHandleForWritingToURL:self.logURL error:error];
    if (!log) return NO;
    self.server.standardOutput = log;
    self.server.standardError = log;
    if (![self.server launchAndReturnError:error]) return NO;

    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        for (NSUInteger attempt = 0; attempt < 100; attempt++) {
            if (!self.server.isRunning) break;
            NSData *data = [NSData dataWithContentsOfURL:self.serverURL];
            if (data.length > 0) {
                dispatch_async(dispatch_get_main_queue(), ^{
                    [self.webView loadRequest:[NSURLRequest requestWithURL:self.serverURL]];
                    self.webView.hidden = NO;
                });
                return;
            }
            [NSThread sleepForTimeInterval:0.1];
        }
        dispatch_async(dispatch_get_main_queue(), ^{
            [self showFailure:[NSString stringWithFormat:@"서버가 시작되지 않았습니다. 로그: %@", self.logURL.path]];
        });
    });
    return YES;
}

- (void)showFailure:(NSString *)message {
    NSAlert *alert = [NSAlert new];
    alert.messageText = @"Founder Atlas 실행 오류";
    alert.informativeText = message;
    [alert runModal];
}

- (void)webView:(WKWebView *)webView decidePolicyForNavigationAction:(WKNavigationAction *)action decisionHandler:(void (^)(WKNavigationActionPolicy))decisionHandler {
    NSURL *url = action.request.URL;
    if ([url.host isEqualToString:@"127.0.0.1"] && url.port.integerValue == self.serverURL.port.integerValue) {
        decisionHandler(WKNavigationActionPolicyAllow);
    } else {
        if (url) [NSWorkspace.sharedWorkspace openURL:url];
        decisionHandler(WKNavigationActionPolicyCancel);
    }
}

- (WKWebView *)webView:(WKWebView *)webView createWebViewWithConfiguration:(WKWebViewConfiguration *)configuration forNavigationAction:(WKNavigationAction *)action windowFeatures:(WKWindowFeatures *)windowFeatures {
    if (action.request.URL) [NSWorkspace.sharedWorkspace openURL:action.request.URL];
    return nil;
}
@end

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSApplication *app = NSApplication.sharedApplication;
        FounderAtlasApp *delegate = [FounderAtlasApp new];
        app.delegate = delegate;
        [app setActivationPolicy:NSApplicationActivationPolicyRegular];
        [app run];
    }
    return 0;
}
