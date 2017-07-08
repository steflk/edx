#include <stdio.h>
#include <stdlib.h>

#include "bmp.h"

int main (int argc, char *argv[]) 
{
    if (argc != 4)
    {
        fprintf(stderr, "Implementation is ./resize int infile outfile\n");
        return 1;
    }
    
    int n = atoi(argv[1]);
    char *infile = argv[2];
    char *outfile = argv[3];
    
    if (n <=0 || n > 100)
    {
        fprintf(stderr, "n must be between 1 and 100 inclusive\n");
        return 1;
    }
    
    FILE *inptr = fopen(infile, "r");
    
    if (inptr == NULL)
    {
        fprintf(stderr, "Infile cannot be read\n");
        return 2;
    }
    
    FILE *outptr = fopen(outfile, "w");
    if (outptr == NULL)
    {
        fclose(inptr);
        fprintf(stderr, "Outfile cannot be written\n");
        return 3;
    }
    
    // read infile's BITMAPFILEHEADER
    BITMAPFILEHEADER bf;
    fread(&bf, sizeof(BITMAPFILEHEADER), 1, inptr);

    // read infile's BITMAPINFOHEADER
    BITMAPINFOHEADER bi;
    fread(&bi, sizeof(BITMAPINFOHEADER), 1, inptr);
    
    BITMAPFILEHEADER new_bf = bf;
    BITMAPINFOHEADER new_bi = bi;

    // ensure infile is (likely) a 24-bit uncompressed BMP 4.0
    if (bf.bfType != 0x4d42 || bf.bfOffBits != 54 || bi.biSize != 40 || 
        bi.biBitCount != 24 || bi.biCompression != 0)
    {
        fclose(outptr);
        fclose(inptr);
        fprintf(stderr, "Unsupported file format.\n");
        return 4;
    }
    
    int padding = (4 - (bi.biWidth * sizeof(RGBTRIPLE)) % 4) % 4;

    new_bi.biWidth = bi.biWidth * n;
    new_bi.biHeight = bi.biHeight * n;
    
    int out_padding = (4 - (new_bi.biWidth * sizeof(RGBTRIPLE)) % 4) % 4;
    
    new_bi.biSizeImage = ((new_bi.biWidth * sizeof(RGBTRIPLE)) + out_padding) * abs(new_bi.biHeight);
    new_bf.bfSize = new_bi.biSizeImage + sizeof(BITMAPFILEHEADER) + sizeof(BITMAPINFOHEADER);

    // write outfile's BITMAPFILEHEADER
    fwrite(&new_bf, sizeof(BITMAPFILEHEADER), 1, outptr);

    // write outfile's BITMAPINFOHEADER
    fwrite(&new_bi, sizeof(BITMAPINFOHEADER), 1, outptr);

    // iterate over infile's scanlines
    for (int i = 0, biHeight = abs(bi.biHeight); i < biHeight; i++)
    {
        for (int m = 0; m < n; m++)
        {
            // iterate over pixels in scanline
            for (int j = 0; j < bi.biWidth; j++)
            {
                // temporary storage
                RGBTRIPLE triple;

                // read RGB triple from infile
                fread(&triple, sizeof(RGBTRIPLE), 1, inptr);
            
                // write each pixel to outfile n times
                for (int y = 0; y < n; y++)
                {
                    fwrite(&triple, sizeof(RGBTRIPLE), 1, outptr);
                }
            }

            // write outfile padding
            for (int x = 0; x < out_padding; x++)
            {
                fputc(0x00, outptr);
            }
            
            if (m < (n-1))
            {
                fseek(inptr, -bi.biWidth * (long int)sizeof(RGBTRIPLE), SEEK_CUR);
            }

        }
        // skip over infile padding, if any
        fseek(inptr, padding, SEEK_CUR);

    }

    // close infile
    fclose(inptr);

    // close outfile
    fclose(outptr);

    // success
    return 0;
}
