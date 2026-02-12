use clap::Parser;

/// Command line arguments parser for this application.
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
pub struct Args {
    /// Start as client, give address to connect.
    #[arg(short, long, default_value = "239.0.0.1:20000")]
    connect_addr: String,

    /// Start as server, give address to listen for connections.
    #[arg(short, long, default_value_t = 0)]
    server_port: u16,
}

impl Args {
    pub fn new() -> Args {
        let args = Args::parse();

        args
    }

    pub fn connect_addr(&self) -> &String {
        &self.connect_addr
    }

    pub fn server_port(&self) -> u16 {
        self.server_port
    }
}
