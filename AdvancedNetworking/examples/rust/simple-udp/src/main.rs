/* Illustrates use of UDP socket, by sending user input to given destination address.
 * Server echoes the datagram content back to client that prints it.
 * 
 * Server usage: cargo run -- -s port
 * Client usage: cargo run -- -c <address:port>
 */

use std::{
    error::Error,
    io::stdin,
    net::UdpSocket,
};

use crate::args::Args;


fn client(args: &Args) -> Result<(), Box<dyn Error>> {
    // Create UDP socket, bind to any address, pick a free UDP port
    let socket = UdpSocket::bind("0.0.0.0:0")?;

    loop {
        let mut input = String::new();
        stdin().read_line(&mut input)?;

        // Send the line given by user to UDP socket, to given destination.
        // Because UDP is not connection-oriented, we use send_to function that
        // provides destination address in addition to data. Unlike with TCP, we
        // can use the same socket for sending to multiple destinations.
        socket.send_to(input.trim().as_bytes(), args.connect_addr())?;

        let mut buf = [0; 1024];
        // Read response back from UDP socket. Blocks execution until datagram
        // arrives. Recv_from returns number of bytes read, and the address/port
        // of the sender.
        let (size, src) = socket.recv_from(&mut buf)?;
        let msg = String::from_utf8_lossy(&buf[..size]);
        println!("Received from {}: {}", src, msg);
    }
}


fn server(args: &Args) -> Result<(), Box<dyn Error>> {
    let socket = UdpSocket::bind(format!("0.0.0.0:{}", args.server_port()))?;

    loop {
        let mut buf = [0; 1024];
        // Block until datagram comes to the socket. Returns number of bytes read
        // and the address/port of the sender.
        // Convert the u8 array into UTF8 string.
        let (size, src) = socket.recv_from(&mut buf)?;
        let msg = String::from_utf8_lossy(&buf[..size]);
        println!("Received from {}: {}", src, msg);

        socket.send_to(&buf, src)?;
    }
}


fn main() -> Result<(), Box<dyn Error>> {
    // Parse command line arguments.
    let args = Args::new();

    if args.server_port() > 0 {
        server(&args)?;
    } else {
        client(&args)?;
    }

    Ok(())  // Everything successful!
}

mod args;
